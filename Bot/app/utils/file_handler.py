import os
import json
import pickle
from pathlib import Path
from typing import Any, Union, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

def save_file(
    data: Any,
    filepath: Union[str, Path],
    file_type: Optional[str] = None,
    create_dirs: bool = True,
    encoding: str = 'utf-8',
    **kwargs
) -> bool:
    """
    Save data to a file with automatic type detection and directory creation.
    
    Args:
        data: The data to save (can be text, dict, list, or any pickle-able object)
        filepath: Path where to save the file
        file_type: Force specific file type ('txt', 'json', 'pickle', 'binary')
                  If None, will auto-detect from file extension
        create_dirs: Whether to create parent directories if they don't exist
        encoding: Text encoding for text files (default: 'utf-8')
        **kwargs: Additional arguments passed to specific save functions
    
    Returns:
        bool: True if save was successful, False otherwise
    
    Examples:
        # Save text
        save_file("Hello World", "output/text.txt")
        
        # Save JSON
        save_file({"key": "value"}, "data/config.json")
        
        # Save binary data
        save_file(b"binary data", "files/data.bin", file_type="binary")
        
        # Save Python object
        save_file([1, 2, 3], "data/list.pkl")
    """
    try:
        filepath = Path(filepath)
        
        # Create parent directories if requested
        if create_dirs and filepath.parent != Path('.'):
            filepath.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directories: {filepath.parent}")
        
        # Determine file type
        if file_type is None:
            file_type = _detect_file_type(filepath, data)
        
        # Save based on file type
        if file_type == 'json':
            return _save_json(data, filepath, encoding, **kwargs)
        elif file_type == 'pickle':
            return _save_pickle(data, filepath, **kwargs)
        elif file_type == 'binary':
            return _save_binary(data, filepath, **kwargs)
        elif file_type == 'txt':
            return _save_text(data, filepath, encoding, **kwargs)
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to save file {filepath}: {str(e)}")
        return False

def _detect_file_type(filepath: Path, data: Any) -> str:
    """Detect file type based on extension and data type."""
    extension = filepath.suffix.lower()
    
    # Extension-based detection
    if extension == '.json':
        return 'json'
    elif extension in ['.pkl', '.pickle']:
        return 'pickle'
    elif extension in ['.bin', '.dat']:
        return 'binary'
    elif extension in ['.txt', '.log', '.md', '.csv']:
        return 'txt'
    
    # Data type-based detection
    if isinstance(data, (dict, list)):
        return 'json'
    elif isinstance(data, (bytes, bytearray)):
        return 'binary'
    elif isinstance(data, str):
        return 'txt'
    else:
        # Default to pickle for complex objects
        return 'pickle'

def _save_json(data: Any, filepath: Path, encoding: str, **kwargs) -> bool:
    """Save data as JSON file."""
    try:
        indent = kwargs.get('indent', 2)
        ensure_ascii = kwargs.get('ensure_ascii', False)
        
        with open(filepath, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        
        logger.info(f"Successfully saved JSON file: {filepath}")
        return True
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization error: {str(e)}")
        return False

def _save_pickle(data: Any, filepath: Path, **kwargs) -> bool:
    """Save data using pickle."""
    try:
        protocol = kwargs.get('protocol', pickle.HIGHEST_PROTOCOL)
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f, protocol=protocol)
        
        logger.info(f"Successfully saved pickle file: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Pickle error: {str(e)}")
        return False

def _save_binary(data: Union[bytes, bytearray], filepath: Path, **kwargs) -> bool:
    """Save binary data."""
    try:
        if not isinstance(data, (bytes, bytearray)):
            logger.error("Binary save requires bytes or bytearray data")
            return False
            
        with open(filepath, 'wb') as f:
            f.write(data)
        
        logger.info(f"Successfully saved binary file: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Binary write error: {str(e)}")
        return False

def _save_text(data: Any, filepath: Path, encoding: str, **kwargs) -> bool:
    """Save data as text file."""
    try:
        # Convert data to string if it isn't already
        if not isinstance(data, str):
            data = str(data)
            
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(data)
        
        logger.info(f"Successfully saved text file: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Text write error: {str(e)}")
        return False

# Additional utility functions
def save_csv(data: list, filepath: Union[str, Path], headers: Optional[list] = None) -> bool:
    """
    Save list of dictionaries or list of lists as CSV.
    
    Args:
        data: List of dictionaries or list of lists
        filepath: Output file path
        headers: Optional headers for list of lists
    """
    try:
        import csv
        filepath = Path(filepath)
        
        if filepath.parent != Path('.'):
            filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if isinstance(data[0], dict):
                # List of dictionaries
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            else:
                # List of lists
                writer = csv.writer(f)
                if headers:
                    writer.writerow(headers)
                writer.writerows(data)
        
        logger.info(f"Successfully saved CSV file: {filepath}")
        return True
    except Exception as e:
        logger.error(f"CSV save error: {str(e)}")
        return False