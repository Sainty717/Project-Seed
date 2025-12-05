# Detailed Guide - Format-Preserving Data Anonymization Framework

Complete documentation with all features, examples, and advanced usage.

## 📖 Table of Contents

1. [Data Types Supported](#data-types-supported)
2. [Anonymization Modes](#anonymization-modes)
3. [Anonymization Profiles](#anonymization-profiles)
4. [Usage Examples](#usage-examples)
5. [Command Reference](#command-reference)
6. [Excel File Support](#excel-file-support)
7. [Python API Usage](#python-api-usage)
8. [Understanding Seeds and Vaults](#understanding-seeds-and-vaults)
9. [Security & Vault Management](#security--vault-management)
10. [Advanced Features](#advanced-features)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Data Types Supported

The framework automatically detects and anonymizes:

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
- **Domains**: Domain-like strings (e.g., `example.onmicrosoft.com`)

---

## Anonymization Modes

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

---

## Anonymization Profiles

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

---

## Usage Examples

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

### Example 4: Multiple Files in One Command (Shared Vault)

```bash
# Process multiple files together - they automatically share the same vault
python -m anonymizer.cli anonymize \
    -i customers.csv \
    -i orders.csv \
    -i products.csv \
    -o output/ \
    --seed my_secret_seed \
    --profile referential_integrity
```

**Result:**
- All files use the same vault automatically
- "John Smith" in `customers.csv` → "Bob Johnson"
- "John Smith" in `orders.csv` → "Bob Johnson" (same mapping!)
- Same values across all files get the same anonymized output
- Maintains relationships across all files

**Benefits:**
- Consistent anonymization across multiple files
- Single vault file for easy management
- All files processed in one session

### Example 5: Using Existing Vault (Reuse Mappings)

```bash
# First run - creates vault
python -m anonymizer.cli anonymize \
    -i customers_sample.csv \
    -o output/ \
    --seed test_seed \
    --profile referential_integrity \
    --interactive \
    --preserve-domain

# Second run - reuse the same vault (same mappings!)
python -m anonymizer.cli anonymize \
    -i new_customers.csv \
    -o output/ \
    --seed test_seed \
    --profile referential_integrity \
    --vault output/20240101_120000/mapping_vault.sqlite \
    --vault-password your_password
```

**Result:**
- Values seen in the first run get the same anonymized output in the second run
- New values are added to the existing vault
- Perfect for incremental processing or adding new files to a project

**Using a Shared Vault Location:**
```bash
# Create a shared vault for your project
python -m anonymizer.cli anonymize \
    -i file1.csv \
    -o output/ \
    --seed project_seed \
    --vault shared_vaults/my_project.sqlite \
    --vault-password my_password

# Add more files to the same project vault
python -m anonymizer.cli anonymize \
    -i file2.csv \
    -o output/ \
    --seed project_seed \
    --vault shared_vaults/my_project.sqlite \
    --vault-password my_password
```

### Example 6: Using Profiles

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

### Example 7: Excel File Support

#### Basic Excel Processing

```bash
# Process Excel file (preserves sheet structure by default)
python -m anonymizer.cli anonymize -i data.xlsx -o output/ --seed my_seed
```

**Result:**
- All sheets processed and preserved in one Excel file
- Original sheet names maintained
- Same structure as input file

#### Interactive Mode for Excel

```bash
# Interactive mode: step through each sheet and select columns
python -m anonymizer.cli anonymize -i data.xlsx -o output/ --seed my_seed --interactive
```

**What happens:**
1. Automatically detects all visible sheets
2. For each sheet:
   - Shows detected columns and types
   - Prompts you to select columns to anonymize
   - You can select different columns for each sheet
3. No need to specify `--sheet` manually

#### Process Specific Sheets

```bash
# Process only selected sheets (still preserves structure)
python -m anonymizer.cli anonymize \
    -i data.xlsx \
    -o output/ \
    --seed my_seed \
    --sheet "Sheet1" \
    --sheet "Sheet2"
```

#### Merge Multiple Sheets into One

```bash
# Merge all sheets into a single sheet
python -m anonymizer.cli anonymize \
    -i data.xlsx \
    -o output/ \
    --seed my_seed \
    --merge-sheets
```

**Result:**
- All sheets combined into one output file
- Adds `_Sheet` column to identify source sheet

#### Write Each Sheet to Separate Files

```bash
# Write each sheet to a separate file
python -m anonymizer.cli anonymize \
    -i data.xlsx \
    -o output/ \
    --seed my_seed \
    --separate-sheets
```

**Result:**
- `data_Sheet1.xlsx`, `data_Sheet2.xlsx`, etc.

#### Excel with Header Row Handling

```bash
# Skip rows and specify header row
python -m anonymizer.cli anonymize \
    -i data.xlsx \
    -o output/ \
    --seed my_seed \
    --skip-rows 2 \
    --header-row 2
```

#### Output Excel as CSV

```bash
# Convert Excel to CSV during anonymization
python -m anonymizer.cli anonymize \
    -i data.xlsx \
    -o output/ \
    --seed my_seed \
    --output-format csv
```

### Example 8: Decrypt Anonymized Data

#### Decrypt CSV File

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

#### Decrypt Excel File (Preserves Sheet Structure)

```bash
# Decrypt Excel file with all sheets (preserves structure)
python -m anonymizer.cli decrypt \
    -i anonymized_data.xlsx \
    -o restored_data.xlsx \
    -v output/20240101_120000/mapping_vault.sqlite \
    -p your_password \
    --seed your_seed

# Decrypt specific sheets only
python -m anonymizer.cli decrypt \
    -i anonymized_data.xlsx \
    -o restored_data.xlsx \
    -v output/20240101_120000/mapping_vault.sqlite \
    -p your_password \
    --seed your_seed \
    --sheet "Sheet1" \
    --sheet "Sheet2"
```

**Features:**
- Auto-detects which columns have mappings
- Preserves unencrypted columns unchanged
- Only decrypts columns that were anonymized
- **Excel**: Preserves all sheet structure and names
- **Excel**: Supports decrypting all sheets or specific sheets

---

## Command Reference

### Anonymize Command

```bash
python -m anonymizer.cli anonymize [OPTIONS]
```

**Options:**
- `-i, --input`: Input file(s) - CSV or Excel (.xlsx, .xls, .xlsm, .xlsb, .ods) (can specify multiple with multiple `-i` flags)
- `-o, --output`: Output directory
- `-p, --profile`: Anonymization profile (default, gdpr_compliant, test_data, fast_hash, referential_integrity)
- `-c, --columns`: Columns to anonymize (can specify multiple, all if not specified)
- `-I, --interactive`: Interactive column selection (for Excel: step through each sheet)
- `-s, --seed`: Deterministic seed for anonymization
- `-m, --mode`: Anonymization mode (fake, fpe, hmac, hybrid)
- `-v, --vault`: Path to existing mapping vault (creates new if not specified)
- `--vault-password`: Password for mapping vault encryption
- `--preserve-domain`: Anonymize domains deterministically (preserve grouping)
- `--no-vault`: Do not store mappings (fully synthetic)
- `--preview/--no-preview`: Show preview before processing (default: true)

**Excel-Specific Options:**
- `--sheet`: Sheet name(s) to process (all sheets if not specified, Excel only)
- `--merge-sheets`: Merge multiple sheets into one sheet (Excel only, default: preserve structure)
- `--separate-sheets`: Write each sheet to a separate file (Excel only, default: preserve structure)
- `--header-row`: Row index (0-based) to use as header (auto-detect if not specified, Excel only)
- `--skip-rows`: Number of rows to skip before reading (Excel only, default: 0)
- `--output-format`: Output format for Excel files - 'excel' or 'csv' (default: 'excel')

### Analyze Command

```bash
# Analyze CSV file
python -m anonymizer.cli analyze -f data.csv [--sample N]

# Analyze Excel file
python -m anonymizer.cli analyze -f data.xlsx [--sheet SHEET_NAME] [--header-row N] [--skip-rows N]
```

Detects data types in CSV or Excel files and shows confidence scores.

**Excel Options:**
- `--sheet`: Sheet name to analyze (uses first sheet if not specified)
- `--header-row`: Row index (0-based) to use as header (auto-detect if not specified)
- `--skip-rows`: Number of rows to skip before reading (default: 0)

### Decrypt Command

```bash
python -m anonymizer.cli decrypt [OPTIONS]
```

**Options:**
- `-i, --input`: Anonymized file to decrypt (CSV or Excel)
- `-o, --output`: Output decrypted file (CSV or Excel)
- `-v, --vault`: Path to mapping vault
- `-p, --password`: Vault password
- `-k, --key-file`: Path to decryption key JSON file
- `-c, --columns`: Columns to decrypt (all anonymized columns if not specified)
- `-s, --seed`: Seed used for anonymization
- `--sheet`: Sheet name(s) to decrypt (Excel only, all sheets if not specified)

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

---

## Excel File Support

### Excel Sheet Handling

The framework provides three modes for handling multiple Excel sheets:

1. **Default (Preserve Structure)**: Writes all sheets to one Excel file, maintaining original sheet names
   ```bash
   python -m anonymizer.cli anonymize -i data.xlsx -o output/
   ```

2. **Merge Sheets**: Combines all sheets into a single sheet
   ```bash
   python -m anonymizer.cli anonymize -i data.xlsx -o output/ --merge-sheets
   ```

3. **Separate Files**: Writes each sheet to a separate file
   ```bash
   python -m anonymizer.cli anonymize -i data.xlsx -o output/ --separate-sheets
   ```

### Excel File Format Support

Supported Excel formats:
- **.xlsx**: Modern Excel format (default)
- **.xls**: Legacy Excel format
- **.xlsm**: Excel with macros
- **.xlsb**: Binary Excel format (requires `pyxlsb`)
- **.ods**: OpenDocument Spreadsheet (requires `odfpy`)

### Excel Header Detection

The framework automatically detects header rows in Excel files:
- Auto-detection: Analyzes first 20 rows to find the header
- Manual specification: Use `--header-row N` to specify exact row (0-based)
- Skip rows: Use `--skip-rows N` to skip blank rows before data

**Example:**
```bash
# Skip 2 blank rows, header is at row 2 (0-based)
python -m anonymizer.cli anonymize -i data.xlsx -o output/ --skip-rows 2 --header-row 2
```

### Excel Interactive Mode

Enhanced interactive mode for Excel files:
- Automatically detects all visible sheets
- Steps through each sheet one by one
- For each sheet:
  - Shows detected columns and types
  - Lets you select columns to anonymize
  - Different column selections per sheet supported
- No need to specify `--sheet` manually
- Perfect for complex Excel files with multiple sheets

**Example:**
```bash
python -m anonymizer.cli anonymize -i data.xlsx -o output/ --interactive
```

---

## Python API Usage

### Basic Example (CSV)

```python
from anonymizer.core.vault import MappingVault
from anonymizer.core.transformers import HybridTransformer
from anonymizer.utils.csv_processor import CSVProcessor

# Initialize components
vault = MappingVault('vault.sqlite', password='my_password')
transformer = HybridTransformer(vault=vault, seed='my_seed')
processor = CSVProcessor(transformer=transformer)

# Process CSV file
processor.process_file(
    'input.csv',
    'output.csv',
    columns_to_anonymize=['name', 'email', 'phone']
)
```

### Excel File Example

```python
from anonymizer.core.vault import MappingVault
from anonymizer.core.transformers import HybridTransformer
from anonymizer.utils.excel_processor import ExcelProcessor

# Initialize components
vault = MappingVault('vault.sqlite', password='my_password')
transformer = HybridTransformer(vault=vault, seed='my_seed')
processor = ExcelProcessor(transformer=transformer)

# Process single sheet
processor.process_sheet(
    'input.xlsx',
    'output.xlsx',
    sheet_name='Sheet1',
    columns_to_anonymize=['name', 'email', 'phone']
)

# Process multiple sheets (preserves structure)
processor.process_multiple_sheets_to_one_file(
    'input.xlsx',
    'output.xlsx',
    sheet_names=['Sheet1', 'Sheet2'],
    columns_to_anonymize={'Sheet1': ['name', 'email'], 'Sheet2': ['phone', 'address']}
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

---

## Understanding Seeds and Vaults

### Seeds Make Anonymization Deterministic

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

### Vaults Store Mappings for Consistency

The **mapping vault** stores all original-to-anonymized value mappings:

- **Same vault = shared mappings**: Multiple files processed together automatically share the same vault
- **Existing vault = reuse mappings**: Use `--vault` to reuse mappings from previous runs
- **Consistency guaranteed**: Same value in same column with same seed = same anonymized output

**Key Points:**
- Multiple files in one command → automatically share the same vault ✅
- Use `--vault` option → reuse mappings from previous sessions ✅
- Same seed + same vault = consistent anonymization across all files ✅

**Important:** 
- Use the same seed when decrypting that you used when anonymizing
- Use the same vault (or vault password) when reusing mappings

---

## Security & Vault Management

### Vault Password

- **With password**: Key derived from password (more secure)
- **Without password**: Random key generated (exported to `decryption_key.json`)

### Decryption Key File

The `decryption_key.json` file contains the actual encryption key. **Keep it secure!**

- Anyone with this file can decrypt your data
- Store separately from the vault
- Consider deleting if you rely on password-only access

### Using Existing Vaults

To reuse mappings from a previous anonymization session:

```bash
# Use an existing vault from a previous run
python -m anonymizer.cli anonymize \
    -i new_file.csv \
    -o output/ \
    --seed your_seed \
    --vault output/20240101_120000/mapping_vault.sqlite \
    --vault-password your_password
```

**Benefits:**
- Values seen before get the same anonymized output
- New values are added to the existing vault
- Perfect for incremental processing or adding files to a project

### Reversibility

- **Reversible modes**: `fake`, `fpe`, `hybrid` (with vault)
- **Non-reversible**: `hmac`, `--no-vault` flag

---

## Advanced Features

### Domain Preservation

When `--preserve-domain` is enabled:
- Domains are anonymized deterministically
- Same original domain → same anonymized domain
- Allows domain-level analytics while protecting individual emails

### Chunked Processing

Large files are automatically processed in chunks (default: 10,000 rows) for memory efficiency.
- CSV files: True chunked streaming
- Excel files: In-memory processing with progress indicators (for very large files, consider converting to CSV first)

### Example Transformations

#### Names
- `John Smith` → `Bob Johnson` (preserves capitalization)
- `JANE DOE` → `ALICE BROWN` (preserves all caps)
- `Mary-Jane Watson` → `Sarah-Kate Miller` (preserves hyphen)

#### Emails
- `john.smith@email.com` → `bob.johnson@example.com`
- With `--preserve-domain`: `john.smith@gmail.com` → `bob.johnson@anonymizedgmail.com`

#### Phone Numbers
- `+61-421-555-829` → `+61-948-221-973` (preserves format)
- `(555) 123-4567` → `(987) 654-3210` (preserves parentheses)

#### Dates
- `1990-01-15` → `1985-06-20` (preserves ISO format)
- `15/01/1990` → `20/06/1985` (preserves DD/MM/YYYY)

---

## Best Practices

1. **Always backup original data** before anonymization
2. **Use strong passwords** for mapping vaults
3. **Store decryption keys securely** if reversibility is needed
4. **Test with preview** before processing large datasets
5. **Use consistent seeds** for referential integrity across files
6. **Review validation reports** after processing
7. **For Excel files**: Use `--interactive` mode to explore sheets and columns before processing
8. **For large Excel files**: Consider converting to CSV first for better performance
9. **Preserve sheet structure**: Default behavior maintains Excel file structure - use `--merge-sheets` or `--separate-sheets` only when needed

---

## Troubleshooting

### Import Errors
- **Issue**: Missing optional dependencies
- **Solution**: Only install what you need. Core functionality works with basic requirements.

### SQLCipher Installation Fails
- **Issue**: SQLCipher installation fails on Windows
- **Solution**: Mapping vault works with standard SQLite. SQLCipher is optional.

### Slow Processing
- **Issue**: Large files process slowly
- **Solution**: Files are processed in chunks automatically. Adjust `chunk_size` in CSVProcessor if needed.

### Excel File Issues

#### "Could not read ODS file"
- **Issue**: Missing `odfpy` library
- **Solution**: Install with `pip install odfpy`

#### "pyxlsb is required for .xlsb files"
- **Issue**: Missing `pyxlsb` library
- **Solution**: Install with `pip install pyxlsb`

#### "Error reading Excel sheet"
- **Issue**: Corrupted file, protected sheet, or unsupported format
- **Solution**: 
  - Check if file is password-protected
  - Try opening in Excel and saving as .xlsx
  - Verify file is not corrupted

#### Excel file too large
- **Issue**: Memory errors when processing very large Excel files
- **Solution**: 
  - Convert to CSV first: `pandas.read_excel()` then `to_csv()`
  - Use `--separate-sheets` to process sheets individually
  - Process in smaller batches

#### "File is not a zip file" or "file size not 512 + multiple of sector size"
- **Issue**: File extension doesn't match actual format
- **Solution**: 
  - Open file in Excel and save as `.xlsx`
  - Check if file is actually `.xls` format (rename and try again)
  - Verify file is not corrupted

---

## Project Structure

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
│   ├── excel_processor.py # Excel processing
│   └── validators.py    # Validation and reporting
└── config/
    ├── __init__.py
    └── profiles.py     # Anonymization profiles
```

---

## Acknowledgments

Built with:
- `pandas` - Data processing
- `cryptography` - Encryption
- `faker` - Fake data generation
- `rich` - Beautiful CLI interface
- `click` - Command-line interface
- `openpyxl` - Excel file support (.xlsx, .xlsm)
- `xlrd` - Legacy Excel support (.xls)

---

**Version**: 1.0.0

For quick reference, see [README.md](README.md)

