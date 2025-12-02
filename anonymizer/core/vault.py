"""
Mapping vault for storing original-to-anonymized value mappings
with encrypted SQLite storage
"""

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64


class MappingVault:
    """Encrypted SQLite vault for storing anonymization mappings"""
    
    def __init__(self, vault_path: str, password: Optional[str] = None):
        """
        Initialize the mapping vault
        
        Args:
            vault_path: Path to SQLite database file
            password: Optional password for encryption (generates key if None)
        """
        self.vault_path = Path(vault_path)
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate or derive encryption key
        if password:
            self.encryption_key = self._derive_key(password)
        else:
            # Generate a new key (should be saved separately)
            self.encryption_key = Fernet.generate_key()
        
        self.cipher = Fernet(self.encryption_key)
        self._init_database()
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        password_bytes = password.encode()
        salt = b'anonymizer_salt_v1'  # In production, use random salt per vault
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def _init_database(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(str(self.vault_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mappings (
                hash_key TEXT PRIMARY KEY,
                original_value TEXT,
                anonymized_value TEXT,
                data_type TEXT,
                column_name TEXT,
                rule_version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hash_key ON mappings(hash_key)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_column_type ON mappings(column_name, data_type)
        ''')
        
        conn.commit()
        conn.close()
    
    def _hash_key(self, original_value: str, column_name: str, seed: Optional[str] = None) -> str:
        """Generate deterministic hash key for lookup"""
        key_string = f"{column_name}:{original_value}"
        if seed:
            key_string = f"{seed}:{key_string}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def store_mapping(
        self,
        original_value: str,
        anonymized_value: str,
        data_type: str,
        column_name: str,
        rule_version: str = "1.0",
        seed: Optional[str] = None
    ):
        """Store a mapping in the vault"""
        hash_key = self._hash_key(original_value, column_name, seed)
        
        # Encrypt values before storage
        encrypted_original = self.cipher.encrypt(original_value.encode())
        encrypted_anonymized = self.cipher.encrypt(anonymized_value.encode())
        
        conn = sqlite3.connect(str(self.vault_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO mappings 
            (hash_key, original_value, anonymized_value, data_type, column_name, rule_version)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            hash_key,
            base64.b64encode(encrypted_original).decode(),
            base64.b64encode(encrypted_anonymized).decode(),
            data_type,
            column_name,
            rule_version
        ))
        
        conn.commit()
        conn.close()
    
    def get_mapping(
        self,
        original_value: str,
        column_name: str,
        seed: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve anonymized value from vault"""
        hash_key = self._hash_key(original_value, column_name, seed)
        
        conn = sqlite3.connect(str(self.vault_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT anonymized_value FROM mappings
            WHERE hash_key = ?
        ''', (hash_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            encrypted_value = base64.b64decode(result[0])
            decrypted_value = self.cipher.decrypt(encrypted_value)
            return decrypted_value.decode()
        
        return None
    
    def reverse_lookup(
        self,
        anonymized_value: str,
        column_name: str,
        seed: Optional[str] = None
    ) -> Optional[str]:
        """Reverse lookup: get original value from anonymized value"""
        conn = sqlite3.connect(str(self.vault_path))
        cursor = conn.cursor()
        
        # Search through all mappings for this column
        cursor.execute('''
            SELECT original_value, anonymized_value FROM mappings
            WHERE column_name = ?
        ''', (column_name,))
        
        for row in cursor.fetchall():
            try:
                encrypted_original = base64.b64decode(row[0])
                encrypted_anonymized = base64.b64decode(row[1])
                
                decrypted_original = self.cipher.decrypt(encrypted_original).decode()
                decrypted_anonymized = self.cipher.decrypt(encrypted_anonymized).decode()
                
                # Check if anonymized value matches
                if decrypted_anonymized == anonymized_value:
                    conn.close()
                    return decrypted_original
            except Exception:
                continue
        
        conn.close()
        return None
    
    def export_key(self, export_path: str):
        """Export encryption key to file (for backup/recovery)"""
        key_data = {
            "encryption_key": base64.b64encode(self.encryption_key).decode(),
            "vault_path": str(self.vault_path)
        }
        
        with open(export_path, 'w') as f:
            json.dump(key_data, f, indent=2)
    
    def load_key(self, key_path: str):
        """Load encryption key from file"""
        with open(key_path, 'r') as f:
            key_data = json.load(f)
        
        self.encryption_key = base64.b64decode(key_data["encryption_key"])
        self.cipher = Fernet(self.encryption_key)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vault statistics"""
        conn = sqlite3.connect(str(self.vault_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM mappings')
        total_mappings = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT data_type, COUNT(*) 
            FROM mappings 
            GROUP BY data_type
        ''')
        type_counts = dict(cursor.fetchall())
        
        cursor.execute('''
            SELECT column_name, COUNT(*) 
            FROM mappings 
            GROUP BY column_name
        ''')
        column_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total_mappings": total_mappings,
            "type_counts": type_counts,
            "column_counts": column_counts
        }

