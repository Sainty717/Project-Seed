# Quick Start Guide

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **(Optional) Install NLP models for advanced detection:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Basic Usage

### 1. Analyze a CSV file

First, see what data types are detected:

```bash
python -m anonymizer.cli analyze -f your_data.csv
```

### 2. Anonymize a file

```bash
python -m anonymizer.cli anonymize -i your_data.csv -o output/
```

This will:
- Detect data types automatically
- Create anonymized version in `output/TIMESTAMP/anonymized_files/`
- Store mapping vault for reversibility
- Generate validation report

### 3. Anonymize specific columns

```bash
python -m anonymizer.cli anonymize -i data.csv -o output/ -c name -c email -c phone
```

### 4. Use a profile

```bash
# GDPR-compliant (reversible with FPE)
python -m anonymizer.cli anonymize -i data.csv -o output/ --profile gdpr_compliant

# Test data generation (fully synthetic)
python -m anonymizer.cli anonymize -i data.csv -o output/ --profile test_data

# Fast hash (non-reversible)
python -m anonymizer.cli anonymize -i data.csv -o output/ --profile fast_hash
```

### 5. Use deterministic seed (for consistency)

```bash
python -m anonymizer.cli anonymize -i data.csv -o output/ --seed my_secret_seed
```

## Example Transformation

**Input CSV:**
```csv
name,email,phone
John Smith,john.smith@email.com,+61-421-555-829
Jane Doe,jane.doe@test.com,+61-422-123-456
```

**Output CSV:**
```csv
name,email,phone
Lork Jenth,lork.jenth@example.com,+61-948-221-973
Kane Moe,kane.moe@demo.net,+61-933-234-567
```

Notice how:
- Names maintain capitalization and structure
- Emails preserve format (local@domain)
- Phone numbers keep formatting characters (+, -, spacing)

## Python API

```python
from anonymizer.core.vault import MappingVault
from anonymizer.core.transformers import HybridTransformer
from anonymizer.utils.csv_processor import CSVProcessor

# Initialize
vault = MappingVault('vault.sqlite', password='password')
transformer = HybridTransformer(vault=vault, seed='my_seed')
processor = CSVProcessor(transformer=transformer)

# Process
processor.process_file('input.csv', 'output.csv', 
                       columns_to_anonymize=['name', 'email'])
```

## Output Structure

```
output/
└── 20240101_120000/
    ├── anonymized_files/     # Your anonymized CSVs
    ├── original_files/        # Backup of originals
    ├── mapping_vault.sqlite   # Encrypted mappings
    ├── format_rules_used.json # Configuration used
    ├── decryption_key.json   # ⚠️ Keep this secure!
    └── validation_report.txt  # Processing summary
```

## Next Steps

- Read [USAGE.md](USAGE.md) for detailed documentation
- Check [example_usage.py](example_usage.py) for code examples
- Run `python -m anonymizer.cli profiles` to see all available profiles

## Troubleshooting

**Issue:** Import errors for optional dependencies
- **Solution:** Only install what you need. Core functionality works with basic requirements.

**Issue:** SQLCipher installation fails
- **Solution:** Mapping vault works with standard SQLite. SQLCipher is optional for additional encryption.

**Issue:** Slow processing on large files
- **Solution:** Files are processed in chunks automatically. Adjust `chunk_size` in CSVProcessor for optimization.

