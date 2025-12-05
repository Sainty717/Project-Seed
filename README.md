# Format-Preserving Data Anonymization Framework

A powerful Python tool for anonymizing CSV and Excel files while preserving data formats, enabling realistic test data generation, GDPR-compliant pseudonymization, and optional deterministic reversibility.

## 🎯 Key Features

- **Format-Preserving Anonymization**: Maintains structure, length, capitalization, and domain models
- **Intelligent Data Type Detection**: Automatic detection of emails, phones, names, UUIDs, addresses, dates, credit cards, IBANs, and more
- **Multiple Anonymization Modes**: Choose from 4 different transformation strategies
- **Reversible Anonymization**: Encrypted mapping vault for deterministic reversibility
- **Cross-Dataset Integrity**: Maintain referential integrity across multiple files
- **Excel File Support**: Full support for .xlsx, .xls, .xlsm, .xlsb, and .ods files with multi-sheet handling
- **Full Decryption Support**: Restore anonymized data back to original values

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Analyze Your Data

```bash
# Analyze CSV file
python -m anonymizer.cli analyze -f data.csv

# Analyze Excel file
python -m anonymizer.cli analyze -f data.xlsx
```

### 2. Basic Anonymization

```bash
# CSV file
python -m anonymizer.cli anonymize -i data.csv -o output/ --vault-password your_password

# Excel file (preserves sheet structure)
python -m anonymizer.cli anonymize -i data.xlsx -o output/ --seed my_seed --vault-password your_password
```

### 3. Decrypt Anonymized Data

```bash
# Decrypt CSV
python -m anonymizer.cli decrypt \
    -i anonymized_data.csv \
    -o restored_data.csv \
    -v output/20240101_120000/mapping_vault.sqlite \
    -p your_password \
    --seed your_seed

# Decrypt Excel (preserves sheet structure)
python -m anonymizer.cli decrypt \
    -i anonymized_data.xlsx \
    -o restored_data.xlsx \
    -v output/20240101_120000/mapping_vault.sqlite \
    -p your_password \
    --seed your_seed
```

## 📖 Common Examples

### Interactive Column Selection

```bash
python -m anonymizer.cli anonymize -i data.csv -o output/ --interactive -p your_password --seed my_seed
```

### Preserve Domain Grouping

```bash
python -m anonymizer.cli anonymize -i data.csv -o output/ --preserve-domain -p your_password --seed my_seed
```

**Result:** `john.smith@gmail.com` → `fakeuser@anonymizedgmail.com`  
Same domain emails get the same anonymized domain, allowing domain-level analytics.

### Multiple Files (Shared Vault)

```bash
python -m anonymizer.cli anonymize \
    -i customers.csv \
    -i orders.csv \
    -i products.csv \
    -o output/ \
    --seed my_secret_seed \
    --profile referential_integrity \
    -p your_password --seed my_seed

```

All files automatically share the same vault - same values get the same anonymized output across all files.

### Using Existing Vault

```bash
# First run - creates vault
python -m anonymizer.cli anonymize \
    -i customers_sample.csv \
    -o output/ \
    --seed test_seed \
    --profile referential_integrity\
    -p your_password

# Second run - reuse the same vault
python -m anonymizer.cli anonymize \
    -i new_customers.csv \
    -o output/ \
    --seed test_seed \
    --vault output/{your time stamp}/mapping_vault.sqlite \
    --vault-password your_password
```

### Excel with Multiple Sheets

```bash
# Process all sheets (preserves structure)
python -m anonymizer.cli anonymize -i data.xlsx -o output/ --seed my_seed --vault-password your_password

# Interactive mode: step through each sheet
python -m anonymizer.cli anonymize -i data.xlsx -o output/ --seed my_seed --interactive --vault-password your_password

# Process specific sheets
python -m anonymizer.cli anonymize \
    -i data.xlsx \
    -o output/ \
    --seed my_seed \
    --sheet "Sheet1" \
    --sheet "Sheet2" \
    --vault-password your_password
```

## 🔧 Command Reference

### Anonymize

```bash
python -m anonymizer.cli anonymize [OPTIONS]
```

**Essential Options:**
- `-i, --input`: Input file(s) - CSV or Excel (can specify multiple)
- `-o, --output`: Output directory
- `-s, --seed`: Deterministic seed for anonymization
- `-I, --interactive`: Interactive column selection
- `-p, --profile`: Profile (default, gdpr_compliant, referential_integrity, test_data, fast_hash)
- `-v, --vault`: Path to existing mapping vault
- `--vault-password`: Password for vault encryption
- `--preserve-domain`: Preserve email domain grouping

**Excel Options:**
- `--sheet`: Sheet name(s) to process (all if not specified)
- `--merge-sheets`: Merge all sheets into one
- `--separate-sheets`: Write each sheet to separate files

### Analyze

```bash
python -m anonymizer.cli analyze -f data.csv [--sample N]
python -m anonymizer.cli analyze -f data.xlsx [--sheet SHEET_NAME]
```

### Decrypt

```bash
python -m anonymizer.cli decrypt \
    -i anonymized_file.csv \
    -o restored_file.csv \
    -v vault.sqlite \
    -p password \
    --seed seed
```

### Reverse Lookup

```bash
python -m anonymizer.cli reverse -v output/{your time stamp}/mapping_vault.sqlite -o "John Smith" -c {$columb name} --seed my_seed -p your_password
```

## 🔐 Anonymization Modes

1. **Hybrid** (Recommended): Numeric via FPE, text via fake generation - Best balance
2. **Format-Preserving Fake**: Generates synthetic values matching structure
3. **Format-Preserving Encryption (FPE)**: Cryptographic reversible encryption
4. **Seeded HMAC**: Fast deterministic hashing (non-reversible)

## 📊 Anonymization Profiles

- **default**: Hybrid mode, balanced approach
- **gdpr_compliant**: FPE with reversible mappings
- **referential_integrity**: Maintains cross-dataset consistency
- **test_data**: Fully synthetic, no vault
- **fast_hash**: Fast non-reversible hashing

## 🔑 Understanding Seeds and Vaults

**Seeds** make anonymization deterministic:
- Same seed + same value = same anonymized value
- Required for referential integrity across files

**Vaults** store mappings for consistency:
- Multiple files in one command → automatically share the same vault
- Use `--vault` to reuse mappings from previous runs
- Same seed + same vault = consistent anonymization

**Important:** Use the same seed when decrypting that you used when anonymizing.

## 🗂️ Output Structure

```
output/
└── 20240101_120000/
    ├── anonymized_files/
    │   └── data.csv              # Your anonymized data
    ├── original_files/
    │   └── data.csv              # Backup of originals
    ├── mapping_vault.sqlite      # Encrypted mappings (for reversibility)
    ├── decryption_key.json      # ⚠️ Keep this secure!
    └── validation_report.txt     # Processing summary
```

## 💻 Python API

```python
from anonymizer.core.vault import MappingVault
from anonymizer.core.transformers import HybridTransformer
from anonymizer.utils.csv_processor import CSVProcessor

# Initialize
vault = MappingVault('vault.sqlite', password='my_password')
transformer = HybridTransformer(vault=vault, seed='my_seed')
processor = CSVProcessor(transformer=transformer)

# Process
processor.process_file(
    'input.csv',
    'output.csv',
    columns_to_anonymize=['name', 'email', 'phone']
)
```

## 📝 Best Practices

1. **Always backup original data** before anonymization
2. **Use strong passwords** for mapping vaults
3. **Store decryption keys securely** if reversibility is needed
4. **Use consistent seeds** for referential integrity across files
5. **Use `--interactive` mode** to explore data before processing

## 📚 Documentation

- **[DETAILED_GUIDE.md](DETAILED_GUIDE.md)**: Complete documentation with all features, examples, and advanced usage
- **[USAGE.md](USAGE.md)**: Detailed usage guide
- **[QUICKSTART.md](QUICKSTART.md)**: Quick start guide

## 🐛 Troubleshooting

**Excel file issues?**
- Check file format (try saving as .xlsx in Excel)
- For large files, consider converting to CSV first
- Use `--interactive` to explore sheets first

**Slow processing?**
- Files are automatically processed in chunks
- For very large Excel files, convert to CSV first

**Missing dependencies?**
- Install optional packages: `pip install pyxlsb odfpy` (only if needed)

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

**Version**: 1.0.0

For more information, run `python -m anonymizer.cli --help`  
For detailed documentation, see [DETAILED_GUIDE.md](DETAILED_GUIDE.md)


