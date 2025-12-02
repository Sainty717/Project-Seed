"""
Validation and reporting utilities
"""

from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import json


class ValidationReport:
    """Generate validation reports for anonymization runs"""
    
    def __init__(self, output_dir: str):
        """
        Initialize validation report
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_data = {
            "timestamp": datetime.now().isoformat(),
            "files_processed": [],
            "columns_anonymized": {},
            "statistics": {},
            "errors": []
        }
    
    def add_file_result(
        self,
        file_name: str,
        columns: List[str],
        rows_processed: int,
        errors: List[str] = None
    ):
        """Add result for a processed file"""
        self.report_data["files_processed"].append({
            "file": file_name,
            "rows": rows_processed,
            "columns_anonymized": columns,
            "errors": errors or []
        })
        
        # Update column statistics
        for col in columns:
            if col not in self.report_data["columns_anonymized"]:
                self.report_data["columns_anonymized"][col] = 0
            self.report_data["columns_anonymized"][col] += rows_processed
    
    def add_statistics(self, stats: Dict[str, Any]):
        """Add general statistics"""
        self.report_data["statistics"].update(stats)
    
    def add_error(self, error: str):
        """Add an error to the report"""
        self.report_data["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "error": error
        })
    
    def generate_report(self, filename: str = "validation_report.txt") -> str:
        """
        Generate text report
        
        Args:
            filename: Name of report file
            
        Returns:
            Path to generated report
        """
        report_path = self.output_dir / filename
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("ANONYMIZATION VALIDATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Generated: {self.report_data['timestamp']}\n\n")
            
            f.write("FILES PROCESSED\n")
            f.write("-" * 80 + "\n")
            for file_info in self.report_data["files_processed"]:
                f.write(f"File: {file_info['file']}\n")
                f.write(f"  Rows: {file_info['rows']:,}\n")
                f.write(f"  Columns anonymized: {', '.join(file_info['columns_anonymized'])}\n")
                if file_info['errors']:
                    f.write(f"  Errors: {len(file_info['errors'])}\n")
                f.write("\n")
            
            f.write("\nCOLUMN STATISTICS\n")
            f.write("-" * 80 + "\n")
            for col, count in sorted(self.report_data["columns_anonymized"].items()):
                f.write(f"{col}: {count:,} values anonymized\n")
            
            if self.report_data["statistics"]:
                f.write("\nGENERAL STATISTICS\n")
                f.write("-" * 80 + "\n")
                for key, value in self.report_data["statistics"].items():
                    f.write(f"{key}: {value}\n")
            
            if self.report_data["errors"]:
                f.write("\nERRORS\n")
                f.write("-" * 80 + "\n")
                for error_info in self.report_data["errors"]:
                    f.write(f"[{error_info['timestamp']}] {error_info['error']}\n")
        
        return str(report_path)
    
    def save_json(self, filename: str = "validation_report.json") -> str:
        """
        Save report as JSON
        
        Args:
            filename: Name of JSON file
            
        Returns:
            Path to generated JSON file
        """
        report_path = self.output_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(self.report_data, f, indent=2)
        
        return str(report_path)

