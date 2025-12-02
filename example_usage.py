"""
Example usage of the Format-Preserving Anonymization Framework
"""

import pandas as pd
from pathlib import Path
from anonymizer.core.detector import DataTypeDetector
from anonymizer.core.vault import MappingVault
from anonymizer.core.transformers import HybridTransformer
from anonymizer.utils.csv_processor import CSVProcessor
from anonymizer.config.profiles import get_default_profiles

# Example 1: Basic usage with a simple CSV
def example_basic():
    """Basic anonymization example"""
    print("=" * 80)
    print("Example 1: Basic Anonymization")
    print("=" * 80)
    
    # Create sample data
    data = {
        'name': ['John Smith', 'Jane Doe', 'Bob Johnson'],
        'email': ['john.smith@email.com', 'jane.doe@email.com', 'bob@test.com'],
        'phone': ['+61-421-555-829', '+61-422-123-456', '+61-423-789-012'],
        'id': ['12345', '67890', '11111']
    }
    df = pd.DataFrame(data)
    
    # Save to CSV
    input_file = 'example_input.csv'
    df.to_csv(input_file, index=False)
    print(f"Created sample file: {input_file}")
    
    # Initialize components
    vault = MappingVault('example_vault.sqlite', password='test_password')
    transformer = HybridTransformer(vault=vault, seed='example_seed')
    processor = CSVProcessor(transformer=transformer)
    
    # Process file
    output_file = 'example_output.csv'
    result = processor.process_file(
        input_file,
        output_file,
        columns_to_anonymize=['name', 'email', 'phone', 'id']
    )
    
    print(f"\nProcessed {result['rows_processed']} rows")
    print(f"Output saved to: {output_file}")
    
    # Show results
    output_df = pd.read_csv(output_file)
    print("\nResults:")
    print(output_df)
    
    # Cleanup
    Path(input_file).unlink(missing_ok=True)
    Path(output_file).unlink(missing_ok=True)
    Path('example_vault.sqlite').unlink(missing_ok=True)


# Example 2: Schema detection
def example_schema_detection():
    """Example of automatic schema detection"""
    print("\n" + "=" * 80)
    print("Example 2: Schema Detection")
    print("=" * 80)
    
    # Create sample data with various types
    data = {
        'customer_name': ['Alice Brown', 'Charlie Wilson', 'Diana Prince'],
        'email_address': ['alice@example.com', 'charlie@test.org', 'diana@demo.net'],
        'phone_number': ['+1-555-123-4567', '+44-20-7946-0958', '+61-2-9876-5432'],
        'user_id': ['550e8400-e29b-41d4-a716-446655440000', 
                    '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
                    '6ba7b811-9dad-11d1-80b4-00c04fd430c8'],
        'account_number': ['1234567890', '9876543210', '5555555555'],
        'birth_date': ['1990-01-15', '1985-06-20', '1992-12-25']
    }
    df = pd.DataFrame(data)
    
    input_file = 'example_schema.csv'
    df.to_csv(input_file, index=False)
    
    # Detect schema
    detector = DataTypeDetector()
    processor = CSVProcessor(transformer=None, detector=detector)
    schema = processor.extract_schema(input_file)
    
    print("\nDetected Schema:")
    for column, (data_type, confidence) in schema.items():
        print(f"  {column:20s} -> {data_type.value:15s} (confidence: {confidence:.1%})")
    
    # Cleanup
    Path(input_file).unlink(missing_ok=True)


# Example 3: Using profiles
def example_profiles():
    """Example using predefined profiles"""
    print("\n" + "=" * 80)
    print("Example 3: Using Profiles")
    print("=" * 80)
    
    # Create sample data
    data = {
        'name': ['John Smith', 'Jane Doe'],
        'email': ['john@example.com', 'jane@test.com'],
        'ssn': ['123-45-6789', '987-65-4321']
    }
    df = pd.DataFrame(data)
    
    input_file = 'example_profile.csv'
    df.to_csv(input_file, index=False)
    
    # Get profiles
    profiles = get_default_profiles()
    
    for profile_name, profile in list(profiles.items())[:3]:  # Show first 3
        print(f"\nUsing profile: {profile_name}")
        print(f"  Mode: {profile.mode.value}")
        print(f"  Reversible: {not profile.fully_synthetic}")
        
        # Create transformer
        vault = MappingVault(f'vault_{profile_name}.sqlite', password='test')
        transformer = profile.create_transformer(vault=vault)
        processor = CSVProcessor(transformer=transformer)
        
        # Process
        output_file = f'output_{profile_name}.csv'
        processor.process_file(
            input_file,
            output_file,
            columns_to_anonymize=['name', 'email', 'ssn']
        )
        
        # Show result
        result_df = pd.read_csv(output_file)
        print(f"  Sample result: {result_df['name'].iloc[0]}")
        
        # Cleanup
        Path(output_file).unlink(missing_ok=True)
        Path(f'vault_{profile_name}.sqlite').unlink(missing_ok=True)
    
    # Cleanup
    Path(input_file).unlink(missing_ok=True)


# Example 4: Preview functionality
def example_preview():
    """Example of preview functionality"""
    print("\n" + "=" * 80)
    print("Example 4: Preview Functionality")
    print("=" * 80)
    
    # Create sample data
    data = {
        'name': ['John Smith', 'Jane Doe', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson'],
        'email': ['john@example.com', 'jane@test.com', 'bob@demo.net', 
                  'alice@sample.org', 'charlie@example.com'],
        'phone': ['+1-555-1234', '+1-555-5678', '+1-555-9012', 
                  '+1-555-3456', '+1-555-7890']
    }
    df = pd.DataFrame(data)
    
    input_file = 'example_preview.csv'
    df.to_csv(input_file, index=False)
    
    # Initialize
    vault = MappingVault('preview_vault.sqlite', password='test')
    transformer = HybridTransformer(vault=vault, seed='preview_seed')
    processor = CSVProcessor(transformer=transformer)
    
    # Generate preview
    preview_df = processor.preview_transformation(
        input_file,
        columns_to_anonymize=['name', 'email', 'phone'],
        num_samples=3
    )
    
    print("\nPreview (Original vs Anonymized):")
    print(preview_df.to_string(index=False))
    
    # Cleanup
    Path(input_file).unlink(missing_ok=True)
    Path('preview_vault.sqlite').unlink(missing_ok=True)


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("Format-Preserving Anonymization Framework - Examples")
    print("=" * 80)
    
    try:
        example_basic()
        example_schema_detection()
        example_profiles()
        example_preview()
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()

