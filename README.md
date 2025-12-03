# Format-Preserving Data Anonymization Framework

A powerful Python tool for anonymizing CSV files while preserving data formats, enabling realistic test data generation, GDPR-compliant pseudonymization, and optional deterministic reversibility.

## 🎯 Key Features

### Core Capabilities

- **Format-Preserving Anonymization**: Maintains structure, length, capitalization, and domain models
- **Intelligent Data Type Detection**: Automatic detection of emails, phones, names, UUIDs, addresses, dates, credit cards, IBANs, and more
- **Multiple Anonymization Modes**: Choose from 4 different transformation strategies
- **Reversible Anonymization**: Encrypted mapping vault for deterministic reversibility
- **Cross-Dataset Integrity**: Maintain referential integrity across multiple files
- **Domain-Level Grouping**: Preserve email domain relationships while anonymizing
- **Interactive Column Selection**: User-friendly interface for selecting columns to anonymize
- **Full Decryption Support**: Restore anonymized data back to original values
- **Performance Optimized**: Stream processing and chunked processing for large datasets

### Data Types Supported

- **Emails**: Preserves structure (`local@domain`), optional domain grouping
- **Phone Numbers**: Maintains international formats (`+`, `-`, parentheses, spacing)
- **Names**: Preserves capitalization, syllable count, and spacing
- **UUIDs/GUIDs**: Format-preserving transformation
- **Dates**: Maintains format (DD/MM/YYYY, ISO, etc.) with leap year safety
- **Numeric IDs**: Format-preserving encryption or deterministic shuffling
- **Credit Cards**: Valid Luhn numbers with preserved formatting
- **IBANs**: Banking number anonymization
- **Addresses**: Synthetic address generation
- **Free Text**: Token-preserving replacement

## 📦 Installation

### Basic Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Optional Dependencies

For advanced NLP-based detection (optional):
```bash
python -m spacy download en_core_web_sm
```

## 🚀 Quick Start

### 1. Analyze Your Data

First, see what data types are detected:

```bash
python -m anonymizer.cli analyze -f data.csv
```

### 2. Basic Anonymization

```bash
python -m anonymizer.cli anonymize -i data.csv -o output/
```

This will:
- Automatically detect data types
- Create anonymized version in `output/TIMESTAMP/anonymized_files/`
- Store mapping vault for reversibility
- Generate validation report
- Show preview before processing

## 📖 Usage Examples

### Example 1: Basic Anonymization

**Input CSV (`data.csv`):**
```csv
name,email,phone
John Smith,john.smith@email.com,+61-421-555-829
Jane Doe,jane.doe@test.com,+61-422-123-456
```

**Command:**
```bash
python -m anonymizer.cli anonymize -i data.csv -o output/
```

**Output:**
```csv
name,email,phone
Lork Jenth,lork.jenth@example.com,+61-948-221-973
Kane Moe,kane.moe@demo.net,+61-933-234-567
```

**Notice:**
- Names maintain capitalization and structure
- Emails preserve format (local@domain)
- Phone numbers keep formatting characters (+, -, spacing)

### Example 2: Interactive Column Selection

```bash
python -m anonymizer.cli anonymize -i data.csv -o output/ --interactive
```

This will:
1. Show a table with all columns and detected types
2. Prompt you to select which columns to anonymize
3. Enter column numbers (e.g., `1,2,3`) or `all`

### Example 3: Preserve Domain Grouping

```bash
python -m anonymizer.cli anonymize -i data.csv -o output/ --preserve-domain
```

**Result:**
- `john.smith@gmail.com` → `fakeuser@anonymizedgmail.com`
- `jane.doe@gmail.com` → `fakeuser2@anonymizedgmail.com` (same domain!)
- `bob@yahoo.com` → `fakeuser3@anonymizedyahoo.com` (different domain)

This allows you to:
- Count users per anonymized domain group
- Maintain domain-level relationships
- See distribution patterns

### Example 4: Deterministic Seed (Referential Integrity)

```bash
# Process multiple files with same seed
python -m anonymizer.cli anonymize -i customers.csv orders.csv -o output/ \
    --seed my_secret_seed
```

**Result:**
- "John Smith" in `customers.csv` → "Bob Johnson"
- "John Smith" in `orders.csv` → "Bob Johnson" (same mapping!)
- Maintains relationships across files

### Example 5: Using Profiles

```bash
# GDPR-compliant (reversible with FPE)
python -m anonymizer.cli anonymize -i data.csv -o output/ --profile gdpr_compliant

# Referential integrity (consistent across files)
python -m anonymizer.cli anonymize -i data.csv -o output/ --profile referential_integrity

# Test data generation (fully synthetic, no vault)
python -m anonymizer.cli anonymize -i data.csv -o output/ --profile test_data

# Fast hash (non-reversible)
python -m anonymizer.cli anonymize -i data.csv -o output/ --profile fast_hash
```

### Example 6: Decrypt Anonymized Data

```bash
# Decrypt using vault password
python -m anonymizer.cli decrypt -i anonymized_data.csv -o restored_data.csv \
    -v output/20240101_120000/mapping_vault.sqlite \
    -p your_password \
    --seed your_seed

# Or use the exported key file
python -m anonymizer.cli decrypt -i anonymized_data.csv -o restored_data.csv \
    -v output/20240101_120000/mapping_vault.sqlite \
    -k output/20240101_120000/decryption_key.json \
    --seed your_seed
```

**Features:**
- Auto-detects which columns have mappings
- Preserves unencrypted columns unchanged
- Only decrypts columns that were anonymized

## 🔧 Command Reference

### Anonymize Command

```bash
python -m anonymizer.cli anonymize [OPTIONS]
```

**Options:**
- `-i, --input`: Input CSV file(s) (can specify multiple)
- `-o, --output`: Output directory
- `-p, --profile`: Anonymization profile (default, gdpr_compliant, test_data, fast_hash, referential_integrity)
- `-c, --columns`: Columns to anonymize (can specify multiple, all if not specified)
- `-I, --interactive`: Interactive column selection
- `-s, --seed`: Deterministic seed for anonymization
- `-m, --mode`: Anonymization mode (fake, fpe, hmac, hybrid)
- `--vault-password`: Password for mapping vault encryption
- `--preserve-domain`: Anonymize domains deterministically (preserve grouping)
- `--no-vault`: Do not store mappings (fully synthetic)
- `--preview/--no-preview`: Show preview before processing (default: true)

### Analyze Command

```bash
python -m anonymizer.cli analyze -f data.csv [--sample N]
```

Detects data types in CSV files and shows confidence scores.

### Decrypt Command

```bash
python -m anonymizer.cli decrypt [OPTIONS]
```

**Options:**
- `-i, --input`: Anonymized CSV file to decrypt
- `-o, --output`: Output decrypted CSV file
- `-v, --vault`: Path to mapping vault
- `-p, --password`: Vault password
- `-k, --key-file`: Path to decryption key JSON file
- `-c, --columns`: Columns to decrypt (all anonymized columns if not specified)
- `-s, --seed`: Seed used for anonymization

### Reverse Lookup Command

```bash
python -m anonymizer.cli reverse -v vault.sqlite -o "John Smith" -c name [--seed seed]
```

Get anonymized value from original (forward lookup).

### Profiles Command

```bash
python -m anonymizer.cli profiles
```

List all available anonymization profiles with descriptions.

## 🔐 Anonymization Modes

### 1. Format-Preserving Fake (fake)
- **Description**: Generates synthetic values matching structure
- **Reversible**: Yes (with vault)
- **Use Case**: Test data generation, realistic anonymization
- **Example**: `john.smith@email.com` → `bob.johnson@example.com`

### 2. Format-Preserving Encryption (fpe)
- **Description**: Cryptographic reversible format-preserving encryption
- **Reversible**: Yes (with vault)
- **Use Case**: GDPR-compliant pseudonymization, secure anonymization
- **Example**: `12345` → `78901` (deterministic encryption)

### 3. Seeded HMAC (hmac)
- **Description**: Fast deterministic hashing
- **Reversible**: No
- **Use Case**: Fast anonymization when reversibility not needed
- **Example**: `john.smith@email.com` → `abc123@xyz789.com` (hash-based)

### 4. Hybrid (hybrid) - **Recommended**
- **Description**: Numeric via FPE, text via fake generation
- **Reversible**: Yes (with vault)
- **Use Case**: Best balance of security and realism
- **Example**: Numbers encrypted, names/emails use fake data

## 📊 Anonymization Profiles

### Default
- **Mode**: Hybrid
- **Reversible**: Yes
- **Description**: Balanced approach for general use

### GDPR Compliant
- **Mode**: FPE
- **Reversible**: Yes
- **Description**: Format-preserving encryption with reversible mappings

### Test Data
- **Mode**: Format-Preserving Fake
- **Reversible**: No (fully synthetic)
- **Description**: Synthetic data generation for testing

### Fast Hash
- **Mode**: Seeded HMAC
- **Reversible**: No
- **Description**: Fast non-reversible hashing

### Referential Integrity
- **Mode**: Hybrid
- **Reversible**: Yes
- **Seed**: `consistent_seed` (pre-configured)
- **Description**: Maintains cross-dataset consistency

## 🗂️ Output Structure

```
output/
└── 20240101_120000/
    ├── anonymized_files/
    │   └── data.csv              # Your anonymized data
    ├── original_files/
    │   └── data.csv              # Backup of originals
    ├── mapping_vault.sqlite      # Encrypted mappings (for reversibility)
    ├── format_rules_used.json   # Configuration used
    ├── decryption_key.json      # ⚠️ Keep this secure!
    └── validation_report.txt     # Processing summary
```

## 💻 Python API Usage

### Basic Example

```python
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

## 🔑 Understanding Seeds

The `--seed` parameter makes anonymization **deterministic**:

- **Same seed + same value = same anonymized value**
- **Different seeds = different mappings**
- **Required for referential integrity across files**

**Example:**
```bash
# Without seed (random each time)
python -m anonymizer.cli anonymize -i data.csv -o output1/
# "John Smith" → "Alice Brown"

python -m anonymizer.cli anonymize -i data.csv -o output2/
# "John Smith" → "Charlie Wilson" (different!)

# With seed (deterministic)
python -m anonymizer.cli anonymize -i data.csv -o output1/ --seed my_seed
# "John Smith" → "Bob Johnson"

python -m anonymizer.cli anonymize -i data.csv -o output2/ --seed my_seed
# "John Smith" → "Bob Johnson" (same!)
```

**Important:** Use the same seed when decrypting that you used when anonymizing!

## 🔒 Security & Vault Management

### Vault Password

- **With password**: Key derived from password (more secure)
- **Without password**: Random key generated (exported to `decryption_key.json`)

### Decryption Key File

The `decryption_key.json` file contains the actual encryption key. **Keep it secure!**

- Anyone with this file can decrypt your data
- Store separately from the vault
- Consider deleting if you rely on password-only access

### Reversibility

- **Reversible modes**: `fake`, `fpe`, `hybrid` (with vault)
- **Non-reversible**: `hmac`, `--no-vault` flag

## 📁 Project Structure

```
anonymizer/
├── __init__.py
├── __main__.py
├── cli.py              # CLI interface with rich UI
├── core/
│   ├── __init__.py
│   ├── detector.py     # Data type detection
│   ├── transformers.py # Format-preserving transformers
│   └── vault.py        # Encrypted mapping vault
├── utils/
│   ├── __init__.py
│   ├── csv_processor.py # CSV processing with chunking
│   └── validators.py    # Validation and reporting
└── config/
    ├── __init__.py
    └── profiles.py     # Anonymization profiles
```

## 🎨 Example Transformations

### Names
- `John Smith` → `Bob Johnson` (preserves capitalization)
- `JANE DOE` → `ALICE BROWN` (preserves all caps)
- `Mary-Jane Watson` → `Sarah-Kate Miller` (preserves hyphen)

### Emails
- `john.smith@email.com` → `bob.johnson@example.com`
- With `--preserve-domain`: `john.smith@gmail.com` → `bob.johnson@anonymizedgmail.com`

### Phone Numbers
- `+61-421-555-829` → `+61-948-221-973` (preserves format)
- `(555) 123-4567` → `(987) 654-3210` (preserves parentheses)

### Dates
- `1990-01-15` → `1985-06-20` (preserves ISO format)
- `15/01/1990` → `20/06/1985` (preserves DD/MM/YYYY)

## ⚙️ Advanced Features

### Domain Preservation

When `--preserve-domain` is enabled:
- Domains are anonymized deterministically
- Same original domain → same anonymized domain
- Allows domain-level analytics while protecting individual emails

### Interactive Mode

Use `--interactive` for guided column selection:
- Shows detected types and confidence scores
- Select columns by number or name
- Perfect for exploring your data first

### Chunked Processing

Large files are automatically processed in chunks (default: 10,000 rows) for memory efficiency.

## 📝 Best Practices

1. **Always backup original data** before anonymization
2. **Use strong passwords** for mapping vaults
3. **Store decryption keys securely** if reversibility is needed
4. **Test with preview** before processing large datasets
5. **Use consistent seeds** for referential integrity across files
6. **Review validation reports** after processing

## 🐛 Troubleshooting

### Import Errors
- **Issue**: Missing optional dependencies
- **Solution**: Only install what you need. Core functionality works with basic requirements.

### SQLCipher Installation Fails
- **Issue**: SQLCipher installation fails on Windows
- **Solution**: Mapping vault works with standard SQLite. SQLCipher is optional.

### Slow Processing
- **Issue**: Large files process slowly
- **Solution**: Files are processed in chunks automatically. Adjust `chunk_size` in CSVProcessor if needed.

## 📚 Additional Documentation

- **[USAGE.md](USAGE.md)**: Detailed usage guide
- **[QUICKSTART.md](QUICKSTART.md)**: Quick start guide
- **[example_usage.py](example_usage.py)**: Python API examples

## 🤝 Contributing

This is a comprehensive anonymization framework. Feel free to extend it with:
- Additional data type detectors
- Custom transformation rules
- New anonymization modes
- Performance optimizations

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- `pandas` - Data processing
- `cryptography` - Encryption
- `faker` - Fake data generation
- `rich` - Beautiful CLI interface
- `click` - Command-line interface

---

**Version**: 1.0.0

For more information, run `python -m anonymizer.cli --help`
