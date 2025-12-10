"""
Format-preserving transformation engines
"""

import hashlib
import random
import re
import string
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from faker import Faker
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import pandas as pd

from .detector import DataType
from .vault import MappingVault


class FormatPreservingTransformer(ABC):
    """Base class for format-preserving transformers"""
    
    def __init__(self, vault: Optional[MappingVault] = None, seed: Optional[str] = None, preserve_domain: bool = False):
        self.vault = vault
        self.seed = seed
        self.preserve_domain = preserve_domain
        self.faker = Faker()
        if seed:
            Faker.seed(hash(seed) % (2**32))
            random.seed(hash(seed))
    
    @abstractmethod
    def transform(
        self,
        value: str,
        data_type: DataType,
        column_name: str,
        **kwargs
    ) -> str:
        """Transform a value while preserving format"""
        pass
    
    def _preserve_format(self, original: str, replacement: str) -> str:
        """Preserve capitalization and structure of original string"""
        if not original:
            return replacement
        
        result = []
        for i, char in enumerate(original):
            if i < len(replacement):
                if char.isupper():
                    result.append(replacement[i].upper())
                elif char.islower():
                    result.append(replacement[i].lower())
                else:
                    result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _anonymize_domain(self, domain: str) -> str:
        """Anonymize domain deterministically while preserving domain grouping"""
        # Use a special column name for domain mappings to keep them separate
        domain_column = "__domain__"
        
        # Check vault first for deterministic mapping
        if self.vault:
            cached = self.vault.get_mapping(domain, domain_column, self.seed)
            if cached:
                return cached
        
        # Generate fake domain deterministically
        if self.seed:
            # Use seed + domain for deterministic generation
            random.seed(hash(f"{self.seed}:{domain}") % (2**32))
            Faker.seed(hash(f"{self.seed}:{domain}") % (2**32))
        
        # Generate fake domain
        fake_domain = self.faker.domain_name()
        
        # Preserve TLD if original had one
        if '.' in domain:
            original_tld = domain.split('.')[-1]
            # Try to preserve TLD structure
            fake_parts = fake_domain.split('.')
            if len(fake_parts) > 1:
                fake_domain = '.'.join(fake_parts[:-1]) + '.' + original_tld
            else:
                fake_domain = fake_domain + '.' + original_tld
        
        # Store in vault if available
        if self.vault:
            self.vault.store_mapping(
                domain,
                fake_domain,
                "domain",
                domain_column,
                seed=self.seed
            )
        
        # Reset seed to original if it was changed
        if self.seed:
            random.seed(hash(self.seed) % (2**32))
            Faker.seed(hash(self.seed) % (2**32))
        
        return fake_domain


class FormatPreservingFakeTransformer(FormatPreservingTransformer):
    """Generates synthetic values while matching structure, casing & grammar"""
    
    def transform(
        self,
        value: str,
        data_type: DataType,
        column_name: str,
        **kwargs
    ) -> str:
        """Transform using format-preserving fake data generation"""
        
        # Check vault first for deterministic mapping
        if self.vault and value is not None:
            try:
                value_str = str(value).strip()
                if value_str:
                    cached = self.vault.get_mapping(value_str, column_name, self.seed)
                    if cached:
                        return cached
            except (TypeError, ValueError):
                pass
        
        # Handle None, NaN, or empty values
        if value is None:
            return value
        try:
            if pd.isna(value):
                return value
        except (TypeError, ValueError):
            pass
        
        value_str = str(value).strip()
        if not value_str:
            return value
        
        # Generate based on data type
        if data_type == DataType.EMAIL:
            result = self._transform_email(value_str)
        elif data_type == DataType.DOMAIN:
            result = self._transform_domain(value_str)
        elif data_type == DataType.PHONE:
            result = self._transform_phone(value_str)
        elif data_type == DataType.NAME:
            result = self._transform_name_with_collision_check(value_str, column_name)
        elif data_type == DataType.UUID or data_type == DataType.GUID:
            result = self._transform_uuid(value_str)
        elif data_type == DataType.DATE:
            result = self._transform_date(value_str)
        elif data_type == DataType.NUMERIC_ID:
            result = self._transform_numeric_id(value_str)
        elif data_type == DataType.ADDRESS:
            result = self._transform_address(value_str)
        elif data_type == DataType.CREDIT_CARD:
            result = self._transform_credit_card(value_str)
        elif data_type == DataType.IBAN:
            result = self._transform_iban(value_str)
        else:
            result = self._transform_free_text(value_str)
        
        # Store in vault if available
        if self.vault:
            self.vault.store_mapping(
                value_str,
                result,
                data_type.value,
                column_name,
                seed=self.seed
            )
        
        return result
    
    def _transform_email(self, value: str) -> str:
        """Transform email while preserving structure"""
        if '@' not in value:
            return value
        
        local, domain = value.split('@', 1)
        
        # Generate fake local part
        fake_local = self.faker.user_name()[:len(local)]
        fake_local = self._preserve_format(local, fake_local)
        
        # Handle domain anonymization
        if self.preserve_domain:
            # Anonymize domain deterministically (same domain → same anonymized domain)
            fake_domain = self._anonymize_domain(domain)
        else:
            # Generate completely new fake domain
            fake_domain = self.faker.domain_name()
        
        return f"{fake_local}@{fake_domain}"
    
    def _transform_phone(self, value: str) -> str:
        """Transform phone while preserving format characters"""
        # Extract digits
        digits = re.sub(r'\D', '', value)
        if not digits:
            return value
        
        # Generate new digits
        new_digits = ''.join(str(random.randint(0, 9)) for _ in digits)
        
        # Reconstruct format
        result = value
        digit_pos = 0
        for i, char in enumerate(value):
            if char.isdigit():
                if digit_pos < len(new_digits):
                    result = result[:i] + new_digits[digit_pos] + result[i+1:]
                    digit_pos += 1
        
        return result
    
    def _transform_name_with_collision_check(self, value: str, column_name: str) -> str:
        """
        Transform name with collision detection and deterministic retry.
        
        If a collision is detected (same anonymized name for different source),
        retries with increasing collision_attempt counter for deterministic regeneration.
        """
        max_attempts = 100  # Prevent infinite loops
        
        for attempt in range(max_attempts):
            result = self._transform_name(value, collision_attempt=attempt)
            
            # Check for collision if vault is available
            if self.vault:
                has_collision = self.vault.check_collision(
                    result,
                    value,
                    column_name,
                    self.seed
                )
                
                if not has_collision:
                    # No collision, safe to return
                    return result
                # Collision detected, try again with next attempt number
            else:
                # No vault, no collision checking possible
                return result
        
        # If we exhausted all attempts, return the last generated value
        # (should be very rare with proper pool sizes)
        return result
    
    def _transform_name(self, value: str, collision_attempt: int = 0) -> str:
        """
        Transform name while preserving capitalization and structure.
        
        Args:
            value: Original name to transform
            collision_attempt: Attempt number (0 = first attempt, 1+ = collision retry)
                              Used for deterministic collision resolution
        """
        # Use value-specific seed for determinism (like _anonymize_domain does)
        # Include collision_attempt to generate different values on retry
        original_random_state = None
        original_faker_state = None
        
        if self.seed:
            # Save current state to restore later
            original_random_state = random.getstate()
            # Create deterministic seed based on value + collision attempt
            seed_string = f"{self.seed}:{value}:{collision_attempt}"
            seed_value = hash(seed_string) % (2**32)
            random.seed(seed_value)
            Faker.seed(seed_value)
        
        try:
            words = value.split()
            fake_words = []
            
            for word in words:
                if len(word) == 1:
                    # Preserve initial
                    fake_words.append(word)
                else:
                    fake_name = self.faker.first_name() if len(fake_words) == 0 else self.faker.last_name()
                    fake_word = self._preserve_format(word, fake_name[:len(word)])
                    fake_words.append(fake_word)
            
            return ' '.join(fake_words)
        finally:
            # Restore original random/Faker state if we changed it
            if self.seed and original_random_state is not None:
                random.setstate(original_random_state)
                # Reset Faker to original seed (approximate restoration)
                Faker.seed(hash(self.seed) % (2**32))
    
    def _transform_uuid(self, value: str) -> str:
        """Transform UUID/GUID"""
        return str(self.faker.uuid4())
    
    def _transform_date(self, value: str) -> str:
        """Transform date while preserving format"""
        # Try to parse date
        try:
            # Generate random date in similar range
            fake_date = self.faker.date_between(start_date='-50y', end_date='today')
            
            # Preserve original format
            if '/' in value:
                return fake_date.strftime('%d/%m/%Y')
            elif '-' in value:
                if len(value) == 10:  # YYYY-MM-DD
                    return fake_date.strftime('%Y-%m-%d')
                else:
                    return fake_date.strftime('%d-%m-%Y')
            else:
                return fake_date.strftime('%Y%m%d')
        except:
            return value
    
    def _transform_numeric_id(self, value: str) -> str:
        """Transform numeric ID while preserving length"""
        if not value.isdigit():
            return value
        
        # Generate same-length number
        length = len(value)
        # First digit should not be 0
        first_digit = str(random.randint(1, 9))
        rest_digits = ''.join(str(random.randint(0, 9)) for _ in range(length - 1))
        return first_digit + rest_digits
    
    def _transform_address(self, value: str) -> str:
        """Transform address"""
        return self.faker.address()
    
    def _transform_credit_card(self, value: str) -> str:
        """Transform credit card number (preserve format, generate valid Luhn)"""
        digits = re.sub(r'\D', '', value)
        if not digits:
            return value
        
        # Generate valid Luhn number
        new_card = self.faker.credit_card_number()
        # Preserve formatting
        formatted = new_card
        if ' ' in value:
            formatted = ' '.join(new_card[i:i+4] for i in range(0, len(new_card), 4))
        elif '-' in value:
            formatted = '-'.join(new_card[i:i+4] for i in range(0, len(new_card), 4))
        
        return formatted
    
    def _transform_iban(self, value: str) -> str:
        """Transform IBAN"""
        # Extract country code
        country_code = value[:2] if len(value) >= 2 else 'GB'
        # Generate fake IBAN (simplified)
        return self.faker.iban()
    
    def _transform_domain(self, value: str) -> str:
        """Transform domain-like strings (e.g., gcwhalewatching.onmicrosoft.com)"""
        # Handle domain anonymization
        if self.preserve_domain:
            # Anonymize domain deterministically (same domain → same anonymized domain)
            return self._anonymize_domain(value)
        else:
            # Generate completely new fake domain
            fake_domain = self.faker.domain_name()
            # Preserve TLD if original had one
            if '.' in value:
                original_tld = value.split('.')[-1]
                fake_parts = fake_domain.split('.')
                if len(fake_parts) > 1:
                    fake_domain = '.'.join(fake_parts[:-1]) + '.' + original_tld
                else:
                    fake_domain = fake_domain + '.' + original_tld
            return fake_domain
    
    def _transform_free_text(self, value: str) -> str:
        """Transform free text while preserving structure - handles domains, complex strings, etc."""
        # Check if it looks like a domain (contains dots, alphanumeric)
        if '.' in value and not value.startswith('.') and not value.endswith('.'):
            parts = value.split('.')
            if len(parts) >= 2 and all(p and (p.isalnum() or '-' in p) for p in parts):
                # Treat as domain-like string
                if self.preserve_domain:
                    return self._anonymize_domain(value)
                else:
                    fake_domain = self.faker.domain_name()
                    # Preserve TLD if original had one
                    original_tld = parts[-1] if parts else 'com'
                    fake_parts = fake_domain.split('.')
                    if len(fake_parts) > 1:
                        fake_domain = '.'.join(fake_parts[:-1]) + '.' + original_tld
                    else:
                        fake_domain = fake_domain + '.' + original_tld
                    return fake_domain
        
        # Handle space-separated words
        words = value.split()
        if len(words) > 1:
            fake_words = []
            for word in words:
                if word.isalpha():
                    fake_word = self.faker.word()[:len(word)]
                    fake_word = self._preserve_format(word, fake_word)
                    fake_words.append(fake_word)
                else:
                    # Try to anonymize non-alphabetic words character by character
                    fake_words.append(self._anonymize_string_char_by_char(word))
            return ' '.join(fake_words)
        else:
            # Single word or no spaces - anonymize character by character
            return self._anonymize_string_char_by_char(value)
    
    def _anonymize_string_char_by_char(self, value: str) -> str:
        """Anonymize string character by character while preserving structure"""
        result = []
        for char in value:
            if char.isalnum():
                if char.isdigit():
                    # Replace digit with random digit
                    result.append(str(random.randint(0, 9)))
                elif char.isupper():
                    # Replace uppercase with random uppercase
                    result.append(chr(random.randint(ord('A'), ord('Z'))))
                else:
                    # Replace lowercase with random lowercase
                    result.append(chr(random.randint(ord('a'), ord('z'))))
            else:
                # Preserve special characters
                result.append(char)
        return ''.join(result)


class FPETransformer(FormatPreservingTransformer):
    """Format-Preserving Encryption using AES-FFX (simplified implementation)"""
    
    def __init__(self, vault: Optional[MappingVault] = None, seed: Optional[str] = None, key: Optional[bytes] = None, preserve_domain: bool = False):
        super().__init__(vault, seed, preserve_domain)
        if key:
            self.key = key
        else:
            # Generate key from seed or random
            if seed:
                key_material = hashlib.sha256(seed.encode()).digest()
            else:
                key_material = hashlib.sha256(str(random.random()).encode()).digest()
            self.key = key_material[:16]  # AES-128
    
    def transform(
        self,
        value: str,
        data_type: DataType,
        column_name: str,
        **kwargs
    ) -> str:
        """Transform using Format-Preserving Encryption"""
        
        # Normalize value for consistent vault lookups
        if value is not None:
            value_str = str(value).strip()
        else:
            value_str = None
        
        if not value_str:
            return value
        
        # Check vault first for deterministic mapping (using normalized value)
        if self.vault:
            cached = self.vault.get_mapping(value_str, column_name, self.seed)
            if cached:
                return cached
        
        # FPE works best on numeric/alphanumeric data
        if data_type in [DataType.NUMERIC_ID, DataType.CREDIT_CARD, DataType.ABN]:
            result = self._fpe_encrypt_numeric(value_str)
        elif data_type == DataType.EMAIL:
            result = self._fpe_encrypt_email(value_str)
        elif data_type == DataType.DOMAIN:
            result = self._fpe_encrypt_domain(value_str)
        elif data_type == DataType.PHONE:
            result = self._fpe_encrypt_phone(value_str)
        else:
            # Fallback to character-level FPE
            result = self._fpe_encrypt_string(value_str)
        
        if self.vault:
            self.vault.store_mapping(
                value_str,
                result,
                data_type.value,
                column_name,
                seed=self.seed
            )
        
        return result
    
    def _fpe_encrypt_numeric(self, value: str) -> str:
        """FPE for numeric strings"""
        digits = re.sub(r'\D', '', value)
        if not digits:
            return value
        
        # Simplified FPE: use deterministic shuffle based on encryption
        # In production, use proper FFX mode
        num = int(digits)
        # Use simple modular arithmetic (not cryptographically secure, but deterministic)
        if self.seed:
            random.seed(hash(self.seed + digits) % (2**32))
        encrypted_num = (num * 7919 + 12345) % (10 ** len(digits))  # Simple transformation
        
        encrypted_str = str(encrypted_num).zfill(len(digits))
        
        # Preserve formatting
        result = value
        digit_pos = 0
        for i, char in enumerate(value):
            if char.isdigit():
                if digit_pos < len(encrypted_str):
                    result = result[:i] + encrypted_str[digit_pos] + result[i+1:]
                    digit_pos += 1
        
        return result
    
    def _fpe_encrypt_email(self, value: str) -> str:
        """FPE for email addresses"""
        if '@' not in value:
            return value
        
        local, domain = value.split('@', 1)
        encrypted_local = self._fpe_encrypt_string(local)
        
        # Handle domain anonymization
        if self.preserve_domain:
            # Anonymize domain deterministically
            encrypted_domain = self._anonymize_domain(domain)
        else:
            encrypted_domain = self._fpe_encrypt_string(domain)
        
        return f"{encrypted_local}@{encrypted_domain}"
    
    def _fpe_encrypt_phone(self, value: str) -> str:
        """FPE for phone numbers"""
        return self._fpe_encrypt_numeric(value)
    
    def _fpe_encrypt_domain(self, value: str) -> str:
        """FPE for domain addresses"""
        if self.preserve_domain:
            # Anonymize domain deterministically
            return self._anonymize_domain(value)
        else:
            # Encrypt the domain character by character
            return self._fpe_encrypt_string(value)
    
    def _fpe_encrypt_string(self, value: str) -> str:
        """FPE for general strings (character-level)"""
        result = []
        for char in value:
            if char.isalnum():
                # Simple character substitution (not cryptographically secure)
                if char.isdigit():
                    new_char = str((int(char) + 5) % 10)
                elif char.isupper():
                    idx = ord(char) - ord('A')
                    new_idx = (idx + 13) % 26
                    new_char = chr(ord('A') + new_idx)
                else:
                    idx = ord(char) - ord('a')
                    new_idx = (idx + 13) % 26
                    new_char = chr(ord('a') + new_idx)
                result.append(new_char)
            else:
                result.append(char)
        
        return ''.join(result)


class SeededHMACTransformer(FormatPreservingTransformer):
    """Deterministic hash-based transformer (not reversible)"""
    
    def transform(
        self,
        value: str,
        data_type: DataType,
        column_name: str,
        **kwargs
    ) -> str:
        """Transform using seeded HMAC"""
        
        if not value:
            return value
        
        value_str = str(value).strip()
        seed_str = f"{self.seed or 'default'}:{column_name}:{value_str}"
        
        # Generate hash
        hash_obj = hashlib.sha256(seed_str.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Map to format-preserving output
        if data_type == DataType.EMAIL:
            return self._hash_to_email(hash_hex, value_str)
        elif data_type == DataType.DOMAIN:
            return self._hash_to_domain(hash_hex, value_str)
        elif data_type == DataType.PHONE:
            return self._hash_to_phone(hash_hex, value_str)
        elif data_type == DataType.NAME:
            return self._hash_to_name(hash_hex, value_str)
        elif data_type == DataType.NUMERIC_ID:
            return self._hash_to_numeric(hash_hex, value_str)
        else:
            return self._hash_to_string(hash_hex, value_str)
    
    def _hash_to_email(self, hash_hex: str, original: str) -> str:
        """Convert hash to email format"""
        if '@' not in original:
            return original
        
        local, domain = original.split('@', 1)
        local_hash = hash_hex[:len(local)]
        
        # Map hex to alphanumeric for local part
        local_part = ''.join(chr(ord('a') + int(c, 16)) for c in local_hash[:len(local)])
        
        # Handle domain anonymization
        if self.preserve_domain:
            # Anonymize domain deterministically using hash of domain
            domain_seed = f"{self.seed or 'default'}:__domain__:{domain}"
            domain_hash_obj = hashlib.sha256(domain_seed.encode())
            domain_hash_hex = domain_hash_obj.hexdigest()
            domain_part = ''.join(chr(ord('a') + int(c, 16)) for c in domain_hash_hex[:len(domain)])
            # Preserve TLD if original had one
            if '.' in domain:
                original_tld = domain.split('.')[-1]
                domain_part = domain_part + '.' + original_tld
            else:
                domain_part = domain_part + '.com'
        else:
            # Original behavior: use hash for domain
            domain_hash = hash_hex[len(local):len(local)+len(domain)]
            domain_part = ''.join(chr(ord('a') + int(c, 16)) for c in domain_hash[:len(domain)])
            domain_part = domain_part + '.com'
        
        return f"{local_part}@{domain_part}"
    
    def _hash_to_domain(self, hash_hex: str, original: str) -> str:
        """Convert hash to domain format"""
        if self.preserve_domain:
            # Anonymize domain deterministically using hash of domain
            domain_seed = f"{self.seed or 'default'}:__domain__:{original}"
            domain_hash_obj = hashlib.sha256(domain_seed.encode())
            domain_hash_hex = domain_hash_obj.hexdigest()
            
            # Generate domain-like string from hash
            parts = original.split('.')
            fake_parts = []
            
            for i, part in enumerate(parts[:-1]):  # All but TLD
                hash_part = domain_hash_hex[i*8:(i+1)*8]
                fake_part = ''.join(chr(ord('a') + int(c, 16) % 26) for c in hash_part[:len(part)])
                fake_parts.append(fake_part)
            
            # Preserve TLD
            original_tld = parts[-1] if parts else 'com'
            fake_parts.append(original_tld)
            
            return '.'.join(fake_parts)
        else:
            # Use hash to generate domain
            parts = original.split('.')
            fake_parts = []
            
            for i, part in enumerate(parts[:-1]):  # All but TLD
                hash_part = hash_hex[i*8:(i+1)*8]
                fake_part = ''.join(chr(ord('a') + int(c, 16) % 26) for c in hash_part[:len(part)])
                fake_parts.append(fake_part)
            
            # Generate random TLD or preserve
            original_tld = parts[-1] if parts else 'com'
            fake_parts.append(original_tld)
            
            return '.'.join(fake_parts)
    
    def _hash_to_phone(self, hash_hex: str, original: str) -> str:
        """Convert hash to phone format"""
        digits = re.sub(r'\D', '', original)
        if not digits:
            return original
        
        # Extract digits from hash
        phone_digits = ''.join(str(int(c, 16) % 10) for c in hash_hex[:len(digits)])
        
        # Preserve format
        result = original
        digit_pos = 0
        for i, char in enumerate(original):
            if char.isdigit():
                if digit_pos < len(phone_digits):
                    result = result[:i] + phone_digits[digit_pos] + result[i+1:]
                    digit_pos += 1
        
        return result
    
    def _hash_to_name(self, hash_hex: str, original: str) -> str:
        """Convert hash to name format"""
        words = original.split()
        name_parts = []
        
        for i, word in enumerate(words):
            hash_part = hash_hex[i*8:(i+1)*8]
            name_part = ''.join(chr(ord('A') + int(c, 16)) for c in hash_part[:len(word)])
            name_part = self._preserve_format(word, name_part)
            name_parts.append(name_part)
        
        return ' '.join(name_parts)
    
    def _hash_to_numeric(self, hash_hex: str, original: str) -> str:
        """Convert hash to numeric format"""
        digits = re.sub(r'\D', '', original)
        if not digits:
            return original
        
        numeric_str = ''.join(str(int(c, 16) % 10) for c in hash_hex[:len(digits)])
        return numeric_str.zfill(len(digits))
    
    def _hash_to_string(self, hash_hex: str, original: str) -> str:
        """Convert hash to string format"""
        result = []
        for i, char in enumerate(original):
            if i < len(hash_hex):
                if char.isalnum():
                    hex_char = hash_hex[i]
                    if char.isdigit():
                        new_char = str(int(hex_char, 16) % 10)
                    elif char.isupper():
                        new_char = chr(ord('A') + int(hex_char, 16) % 26)
                    else:
                        new_char = chr(ord('a') + int(hex_char, 16) % 26)
                    result.append(new_char)
                else:
                    result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)


class HybridTransformer(FormatPreservingTransformer):
    """Hybrid transformer: Numeric via FPE, text via FPT"""
    
    def __init__(self, vault: Optional[MappingVault] = None, seed: Optional[str] = None, preserve_domain: bool = False):
        super().__init__(vault, seed, preserve_domain)
        self.fpe_transformer = FPETransformer(vault, seed, preserve_domain=preserve_domain)
        self.fpt_transformer = FormatPreservingFakeTransformer(vault, seed, preserve_domain=preserve_domain)
    
    def transform(
        self,
        value: str,
        data_type: DataType,
        column_name: str,
        **kwargs
    ) -> str:
        """Transform using hybrid approach"""
        
        # Use FPE for numeric data types
        if data_type in [DataType.NUMERIC_ID, DataType.CREDIT_CARD, DataType.ABN, DataType.IBAN]:
            return self.fpe_transformer.transform(value, data_type, column_name, **kwargs)
        else:
            # Use FPT for text-based data types
            return self.fpt_transformer.transform(value, data_type, column_name, **kwargs)

