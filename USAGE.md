# Usage Guide

## Installation

```bash
pip install -r requirements.txt
```

For optional NLP features:
```bash
python -m spacy download en_core_web_sm
```

## Command Line Usage

### Basic Anonymization

```bash
# Anonymize a single file
python -m anonymizer.cli anonymize -i data.csv -o output/

# Anonymize multiple files
python -m anonymizer.cli anonymize -i file1.csv file2.csv -o output/

# Specify columns to anonymize
python -m anonymizer.cli anonymize -i data.csv -o output/ -c name -c email -c phone

# Use a specific profile
python -m anonymizer.cli anonymize -i data.csv -o output/ --profile gdpr_compliant

# Use deterministic seed
python -m anonymizer.cli anonymize -i data.csv -o output/ --seed my_secret_seed

# Set vault password
python -m anonymizer.cli anonymize -i data.csv -o output/ --vault-password my_password
```

### Analyze Schema

```bash
# Detect data types in a CSV file
python -m anonymizer.cli analyze -f data.csv

# Sample more rows for better detection
python -m anonymizer.cli analyze -f data.csv --sample 500
```

### Reverse Lookup

```bash
# Get anonymized value from original
python -m anonymizer.cli reverse -v mapping_vault.sqlite -o "John Smith" -c name --seed my_seed
```

### Decrypt Files

```bash
# Decrypt an entire anonymized CSV file
python -m anonymizer.cli decrypt -i anonymized_data.csv -o decrypted_data.csv \
    -v output/20240101_120000/mapping_vault.sqlite \
    -p your_password \
    --seed your_seed

# Or use the exported key file
python -m anonymizer.cli decrypt -i anonymized_data.csv -o decrypted_data.csv \
    -v output/20240101_120000/mapping_vault.sqlite \
    -k output/20240101_120000/decryption_key.json \
    --seed your_seed

# Decrypt specific columns only
python -m anonymizer.cli decrypt -i anonymized_data.csv -o decrypted_data.csv \
    -v mapping_vault.sqlite -p password --seed seed -c name -c email
```

### List Profiles

```bash
# Show available anonymization profiles
python -m anonymizer.cli profiles
```

## Python API Usage

### Basic Example

```python
from anonymizer.core.detector import DataTypeDetector
from anonymizer.core.vault import MappingVault
from anonymizer.core.transformers import HybridTransformer
from anonymizer.utils.csv_processor import CSVProcessor

# Initialize components
vault = MappingVault('vault.sqlite', password='my_password')
transformer = HybridTransformer(vault=vault, seed='my_seed')
processor = CSVProcessor(transformer=transformer)

# Process file
processor.process_file(
    'input.csv',
    'output.csv',
    columns_to_anonymize=['name', 'email', 'phone']
)
```

### Using Profiles

```python
from anonymizer.config.profiles import get_default_profiles

profiles = get_default_profiles()
profile = profiles['gdpr_compliant']

transformer = profile.create_transformer(vault=vault)
processor = CSVProcessor(transformer=transformer)
```

### Schema Detection

```python
from anonymizer.core.detector import DataTypeDetector
from anonymizer.utils.csv_processor import CSVProcessor

detector = DataTypeDetector()
processor = CSVProcessor(transformer=None, detector=detector)

schema = processor.extract_schema('data.csv', sample_rows=100)
for column, (data_type, confidence) in schema.items():
    print(f"{column}: {data_type.value} ({confidence:.1%})")
```

### Preview Before Processing

```python
preview_df = processor.preview_transformation(
    'data.csv',
    columns_to_anonymize=['name', 'email'],
    num_samples=10
)
print(preview_df)
```

## Anonymization Modes

1. **Format-Preserving Fake (default)**: Generates synthetic values matching structure
2. **FPE**: Format-Preserving Encryption (cryptographically secure)
3. **Seeded HMAC**: Fast deterministic hashing (non-reversible)
4. **Hybrid**: Numeric via FPE, text via fake generation (recommended)

## Output Structure

```
output/
└── 20240101_120000/
    ├── anonymized_files/
    │   └── data.csv
    ├── original_files/
    │   └── data.csv
    ├── mapping_vault.sqlite
    ├── format_rules_used.json
    ├── decryption_key.json
    └── validation_report.txt
```

## Best Practices

1. **Always backup original data** before anonymization
2. **Use strong passwords** for mapping vaults
3. **Store decryption keys securely** if reversibility is needed
4. **Test with preview** before processing large datasets
5. **Use consistent seeds** for referential integrity across files
6. **Review validation reports** after processing

## Security Notes

- Mapping vaults are encrypted using Fernet (symmetric encryption)
- Keys can be exported for backup/recovery
- Fully synthetic mode doesn't store mappings (not reversible)
- HMAC mode is not reversible by design

