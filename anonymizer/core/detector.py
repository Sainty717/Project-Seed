"""
Data type detection system using pattern matching and heuristics
"""

import re
import uuid
from typing import Dict, Optional, Tuple
from enum import Enum


class DataType(Enum):
    """Supported data types for anonymization"""
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    UUID = "uuid"
    GUID = "guid"
    IBAN = "iban"
    CREDIT_CARD = "credit_card"
    ABN = "abn"
    ADDRESS = "address"
    DATE = "date"
    NUMERIC_ID = "numeric_id"
    FREE_TEXT = "free_text"
    UNKNOWN = "unknown"


class DataTypeDetector:
    """Detects data types in CSV columns using pattern matching and heuristics"""
    
    # Email pattern
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        re.IGNORECASE
    )
    
    # Phone patterns (international)
    PHONE_PATTERNS = [
        re.compile(r'^\+?[1-9]\d{1,14}$'),  # E.164
        re.compile(r'^\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,9}[-.\s]?\d{1,9}$'),
        re.compile(r'^\+?61[-.\s]?\d{1}[-.\s]?\d{4}[-.\s]?\d{4}$'),  # Australian
        re.compile(r'^\+?1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}$'),  # US/Canada
    ]
    
    # UUID/GUID patterns
    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    # IBAN pattern (simplified)
    IBAN_PATTERN = re.compile(r'^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$')
    
    # Credit card patterns
    CREDIT_CARD_PATTERN = re.compile(r'^\d{13,19}$')
    
    # ABN (Australian Business Number) pattern
    ABN_PATTERN = re.compile(r'^\d{11}$')
    
    # Date patterns
    DATE_PATTERNS = [
        re.compile(r'^\d{4}-\d{2}-\d{2}'),  # ISO
        re.compile(r'^\d{2}/\d{2}/\d{4}'),  # DD/MM/YYYY
        re.compile(r'^\d{2}-\d{2}-\d{4}'),  # DD-MM-YYYY
        re.compile(r'^\d{4}/\d{2}/\d{2}'),  # YYYY/MM/DD
    ]
    
    def __init__(self):
        self.detection_cache: Dict[str, DataType] = {}
    
    def detect_column_type(
        self, 
        column_name: str, 
        sample_values: list,
        user_override: Optional[DataType] = None
    ) -> Tuple[DataType, float]:
        """
        Detect the data type of a column
        
        Args:
            column_name: Name of the column
            sample_values: Sample values from the column
            user_override: Optional user-specified type override
            
        Returns:
            Tuple of (detected_type, confidence_score)
        """
        if user_override:
            return user_override, 1.0
        
        # Check cache
        cache_key = f"{column_name}:{len(sample_values)}"
        if cache_key in self.detection_cache:
            return self.detection_cache[cache_key], 0.9
        
        if not sample_values:
            return DataType.UNKNOWN, 0.0
        
        # Filter out None/NaN values
        valid_samples = [v for v in sample_values if v and str(v).strip()]
        if not valid_samples:
            return DataType.UNKNOWN, 0.0
        
        # Check column name hints
        name_lower = column_name.lower()
        type_scores: Dict[DataType, float] = {}
        
        # Email detection
        if 'email' in name_lower or 'e-mail' in name_lower:
            type_scores[DataType.EMAIL] = 0.8
        else:
            email_matches = sum(1 for v in valid_samples[:100] if self.EMAIL_PATTERN.match(str(v)))
            if email_matches > len(valid_samples) * 0.8:
                type_scores[DataType.EMAIL] = email_matches / len(valid_samples)
        
        # Phone detection
        if 'phone' in name_lower or 'tel' in name_lower or 'mobile' in name_lower:
            type_scores[DataType.PHONE] = 0.8
        else:
            phone_matches = sum(
                1 for v in valid_samples[:100] 
                if any(pattern.match(re.sub(r'[^\d+]', '', str(v))) for pattern in self.PHONE_PATTERNS)
            )
            if phone_matches > len(valid_samples) * 0.7:
                type_scores[DataType.PHONE] = phone_matches / len(valid_samples)
        
        # Name detection
        if any(keyword in name_lower for keyword in ['name', 'firstname', 'lastname', 'fullname', 'surname']):
            type_scores[DataType.NAME] = 0.8
        else:
            # Heuristic: names typically have capital letters, spaces, 2-4 words
            name_matches = sum(
                1 for v in valid_samples[:100]
                if self._looks_like_name(str(v))
            )
            if name_matches > len(valid_samples) * 0.6:
                type_scores[DataType.NAME] = name_matches / len(valid_samples)
        
        # UUID/GUID detection
        if 'uuid' in name_lower or 'guid' in name_lower or 'id' in name_lower:
            uuid_matches = sum(
                1 for v in valid_samples[:100]
                if self.UUID_PATTERN.match(str(v).strip())
            )
            if uuid_matches > len(valid_samples) * 0.8:
                type_scores[DataType.UUID if 'uuid' in name_lower else DataType.GUID] = uuid_matches / len(valid_samples)
        
        # IBAN detection
        if 'iban' in name_lower:
            type_scores[DataType.IBAN] = 0.9
        else:
            iban_matches = sum(
                1 for v in valid_samples[:100]
                if self.IBAN_PATTERN.match(str(v).replace(' ', '').upper())
            )
            if iban_matches > len(valid_samples) * 0.7:
                type_scores[DataType.IBAN] = iban_matches / len(valid_samples)
        
        # Credit card detection
        if any(keyword in name_lower for keyword in ['card', 'credit', 'cc']):
            cc_matches = sum(
                1 for v in valid_samples[:100]
                if self.CREDIT_CARD_PATTERN.match(re.sub(r'[^\d]', '', str(v)))
            )
            if cc_matches > len(valid_samples) * 0.7:
                type_scores[DataType.CREDIT_CARD] = cc_matches / len(valid_samples)
        
        # ABN detection
        if 'abn' in name_lower:
            abn_matches = sum(
                1 for v in valid_samples[:100]
                if self.ABN_PATTERN.match(re.sub(r'[^\d]', '', str(v)))
            )
            if abn_matches > len(valid_samples) * 0.7:
                type_scores[DataType.ABN] = abn_matches / len(valid_samples)
        
        # Date detection
        if any(keyword in name_lower for keyword in ['date', 'time', 'dob', 'birth']):
            date_matches = sum(
                1 for v in valid_samples[:100]
                if any(pattern.match(str(v)) for pattern in self.DATE_PATTERNS)
            )
            if date_matches > len(valid_samples) * 0.7:
                type_scores[DataType.DATE] = date_matches / len(valid_samples)
        
        # Numeric ID detection
        if 'id' in name_lower and not type_scores:
            numeric_matches = sum(
                1 for v in valid_samples[:100]
                if str(v).strip().isdigit()
            )
            if numeric_matches > len(valid_samples) * 0.9:
                type_scores[DataType.NUMERIC_ID] = numeric_matches / len(valid_samples)
        
        # Address detection
        if any(keyword in name_lower for keyword in ['address', 'street', 'city', 'postcode', 'zip']):
            type_scores[DataType.ADDRESS] = 0.7
        
        # Determine best match
        if type_scores:
            best_type = max(type_scores.items(), key=lambda x: x[1])
            detected_type, confidence = best_type
            self.detection_cache[cache_key] = detected_type
            return detected_type, confidence
        
        # Default to free text if no strong match
        return DataType.FREE_TEXT, 0.3
    
    def _looks_like_name(self, value: str) -> bool:
        """Heuristic to check if a value looks like a name"""
        if not value or len(value) < 2:
            return False
        
        # Check for proper capitalization
        words = value.split()
        if len(words) < 1 or len(words) > 4:
            return False
        
        # Check if first letter of each word is capitalized
        has_capitalization = all(
            word[0].isupper() if word else False
            for word in words
        )
        
        # Check for reasonable length
        reasonable_length = all(2 <= len(word) <= 20 for word in words)
        
        # Check for alphabetic characters
        is_alphabetic = all(word.isalpha() for word in words)
        
        return has_capitalization and reasonable_length and is_alphabetic
    
    def detect_schema(self, df, sample_size: int = 100) -> Dict[str, Tuple[DataType, float]]:
        """
        Detect schema for all columns in a DataFrame
        
        Args:
            df: pandas/polars DataFrame
            sample_size: Number of samples to use for detection
            
        Returns:
            Dictionary mapping column names to (type, confidence) tuples
        """
        schema = {}
        
        for column in df.columns:
            # Get sample values
            sample_values = df[column].dropna().head(sample_size).tolist()
            data_type, confidence = self.detect_column_type(column, sample_values)
            schema[column] = (data_type, confidence)
        
        return schema

