"""
CSV processing utilities with chunked processing support
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from tqdm import tqdm
import multiprocessing as mp

from ..core.detector import DataTypeDetector, DataType
from ..core.transformers import FormatPreservingTransformer


class CSVProcessor:
    """Process CSV files with schema detection and anonymization"""
    
    def __init__(
        self,
        transformer: FormatPreservingTransformer,
        detector: Optional[DataTypeDetector] = None,
        chunk_size: int = 10000,
        use_multiprocessing: bool = False
    ):
        """
        Initialize CSV processor
        
        Args:
            transformer: Transformer to use for anonymization
            detector: Optional data type detector (creates new if None)
            chunk_size: Size of chunks for processing large files
            use_multiprocessing: Whether to use multiprocessing
        """
        self.transformer = transformer
        self.detector = detector or DataTypeDetector()
        self.chunk_size = chunk_size
        self.use_multiprocessing = use_multiprocessing
    
    def extract_schema(
        self,
        file_path: str,
        sample_rows: int = 100
    ) -> Dict[str, Tuple[DataType, float]]:
        """
        Extract schema from CSV file
        
        Args:
            file_path: Path to CSV file
            sample_rows: Number of rows to sample for detection
            
        Returns:
            Dictionary mapping column names to (type, confidence) tuples
        """
        df_sample = pd.read_csv(file_path, nrows=sample_rows)
        schema = self.detector.detect_schema(df_sample, sample_size=sample_rows)
        return schema
    
    def process_file(
        self,
        input_path: str,
        output_path: str,
        columns_to_anonymize: Optional[List[str]] = None,
        schema_override: Optional[Dict[str, DataType]] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Process a CSV file and anonymize specified columns
        
        Args:
            input_path: Path to input CSV file
            output_path: Path to output CSV file
            schema_override: Optional manual type overrides per column
            columns_to_anonymize: List of column names to anonymize (all if None)
            show_progress: Whether to show progress bar
            
        Returns:
            Dictionary with processing statistics
        """
        input_path_obj = Path(input_path)
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Detect schema
        schema = self.extract_schema(input_path)
        
        # Apply overrides
        if schema_override:
            for col, data_type in schema_override.items():
                if col in schema:
                    schema[col] = (data_type, 1.0)
        
        # Determine columns to process
        if columns_to_anonymize is None:
            columns_to_anonymize = list(schema.keys())
        
        # Filter to only columns that exist
        columns_to_anonymize = [col for col in columns_to_anonymize if col in schema]
        
        # Get file size for progress estimation
        file_size = input_path_obj.stat().st_size
        total_rows = sum(1 for _ in open(input_path, 'r', encoding='utf-8')) - 1  # Exclude header
        
        processed_rows = 0
        chunks_processed = 0
        
        # Process in chunks
        chunk_iter = pd.read_csv(
            input_path,
            chunksize=self.chunk_size,
            iterator=True
        )
        
        first_chunk = True
        
        with tqdm(total=total_rows, desc="Processing", disable=not show_progress) as pbar:
            for chunk in chunk_iter:
                # Anonymize columns
                for column in columns_to_anonymize:
                    if column in chunk.columns:
                        data_type, _ = schema[column]
                        
                        # Apply transformation
                        chunk[column] = chunk[column].apply(
                            lambda x: self.transformer.transform(
                                x,
                                data_type,
                                column
                            ) if pd.notna(x) and str(x).strip() else x
                        )
                
                # Write chunk
                mode = 'w' if first_chunk else 'a'
                header = first_chunk
                chunk.to_csv(
                    output_path,
                    mode=mode,
                    header=header,
                    index=False
                )
                
                first_chunk = False
                processed_rows += len(chunk)
                chunks_processed += 1
                pbar.update(len(chunk))
        
        return {
            "input_file": input_path,
            "output_file": output_path,
            "rows_processed": processed_rows,
            "columns_anonymized": columns_to_anonymize,
            "chunks_processed": chunks_processed
        }
    
    def process_multiple_files(
        self,
        input_files: List[str],
        output_dir: str,
        columns_to_anonymize: Optional[List[str]] = None,
        schema_override: Optional[Dict[str, DataType]] = None,
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple CSV files
        
        Args:
            input_files: List of input file paths
            output_dir: Directory for output files
            columns_to_anonymize: Columns to anonymize
            schema_override: Schema overrides
            show_progress: Whether to show progress
            
        Returns:
            List of processing statistics for each file
        """
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        for input_file in tqdm(input_files, desc="Processing files", disable=not show_progress):
            input_path = Path(input_file)
            output_path = output_dir_path / input_path.name
            
            result = self.process_file(
                str(input_path),
                str(output_path),
                columns_to_anonymize,
                schema_override,
                show_progress=False  # Disable individual progress bars
            )
            results.append(result)
        
        return results
    
    def preview_transformation(
        self,
        file_path: str,
        columns_to_anonymize: Optional[List[str]] = None,
        num_samples: int = 10
    ) -> pd.DataFrame:
        """
        Generate preview of transformations
        
        Args:
            file_path: Path to CSV file
            columns_to_anonymize: Columns to preview
            num_samples: Number of sample rows to show
            
        Returns:
            DataFrame with original and anonymized columns side by side
        """
        df = pd.read_csv(file_path, nrows=num_samples)
        schema = self.extract_schema(file_path)
        
        if columns_to_anonymize is None:
            columns_to_anonymize = list(schema.keys())
        
        preview_data = {}
        
        for column in df.columns:
            preview_data[f"{column}_original"] = df[column]
            
            if column in columns_to_anonymize and column in schema:
                data_type, _ = schema[column]
                preview_data[f"{column}_anonymized"] = df[column].apply(
                    lambda x: self.transformer.transform(
                        x,
                        data_type,
                        column
                    ) if pd.notna(x) and str(x).strip() else x
                )
            else:
                preview_data[f"{column}_anonymized"] = df[column]
        
        return pd.DataFrame(preview_data)

