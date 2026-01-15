import os
import tempfile
from pathlib import Path
from .. import exceptions
from ..services import service_defaults


class PathUtils:
    """
    Utility class for path validation and sanitization to prevent path traversal attacks.
    """
    allowed_roots = [tempfile.gettempdir(), service_defaults.DATALOOP_PATH]
    
    @staticmethod
    def _contains_traversal(path: str) -> bool:
        """
        Check if path contains path traversal sequences.
        
        :param str path: Path to check
        :return: True if path contains traversal sequences
        :rtype: bool
        """
        if not path:
            return False
        
        # Normalize the path to handle different separators
        normalized = os.path.normpath(path)
        
        # Check for parent directory references
        parts = Path(normalized).parts
        if '..' in parts:
            return True
        
        # Check for encoded traversal sequences (evasion attempts)
        if '%2e%2e' in path.lower() or '..%2f' in path.lower() or '..%5c' in path.lower():
            return True
        
        return False
    
    @staticmethod
    def _is_within_base(resolved_path: str, base_path: str) -> bool:
        """
        Check if resolved_path is within base_path.
        
        :param str resolved_path: Absolute resolved path
        :param str base_path: Base directory path
        :return: True if resolved_path is within base_path
        :rtype: bool
        """
        try:
            resolved = os.path.abspath(os.path.normpath(resolved_path))
            base = os.path.abspath(os.path.normpath(base_path))
            
            # Get common path
            common = os.path.commonpath([resolved, base])
            return common == base
        except (ValueError, OSError):
            # On Windows, if paths are on different drives, commonpath raises ValueError
            return False
    
    @staticmethod
    def _is_allowed_path(resolved_path: str, base_path: str) -> bool:
        """
        Check if resolved_path is within base_path or any allowed_root.
        
        :param str resolved_path: Absolute resolved path
        :param str base_path: Base directory path
        :return: True if resolved_path is within base_path or any allowed_root
        :rtype: bool
        """
        for allowed_root in [base_path] + PathUtils.allowed_roots:
            if PathUtils._is_within_base(resolved_path, allowed_root):
                return True
        return False
    
    @staticmethod
    def validate_directory_name(name: str) -> str:
        """
        Validate a directory name to ensure it doesn't contain path traversal sequences.
        
        :param str name: Directory name to validate
        :return: Validated directory name
        :rtype: str
        :raises PlatformException: If name contains invalid characters or traversal sequences
        """
        if not name:
            raise exceptions.PlatformException(
                error='400',
                message='Directory name cannot be empty'
            )
        
        # Check for path separators
        if os.sep in name or (os.altsep and os.altsep in name):
            raise exceptions.PlatformException(
                error='400',
                message='Directory name cannot contain path separators'
            )
        
        # Check for traversal sequences
        if PathUtils._contains_traversal(name):
            raise exceptions.PlatformException(
                error='400',
                message='Directory name cannot contain path traversal sequences'
            )
        
        return name
    
    @staticmethod
    def _validate_single_path(path, base_path: str, must_exist: bool):
        """
        Internal method to validate a single path string.
        
        :param path: Path to validate (str or Path object)
        :param str base_path: Base directory to restrict path to
        :param bool must_exist: If True, path must exist
        :raises PlatformException: If path is invalid or contains traversal sequences
        """
        # Convert Path objects to strings
        if isinstance(path, Path):
            path = str(path)
        if isinstance(base_path, Path):
            base_path = str(base_path)
        
        # Skip validation if not a string
        if not isinstance(path, str):
            return
        
        # Skip validation for URLs and external paths
        if path.startswith(('http://', 'https://', 'external://')):
            return
        
        # Empty string check
        if not path:
            raise exceptions.PlatformException(
                error='400',
                message='Path cannot be empty'
            )
        
        # Check for traversal sequences in the original path
        if PathUtils._contains_traversal(path):
            raise exceptions.PlatformException(
                error='400',
                message='Path contains invalid traversal sequences'
            )
        
        # Resolve path (absolute paths allowed if within base_path)
        if os.path.isabs(path):
            resolved = os.path.abspath(os.path.normpath(path))
        else:
            resolved = os.path.abspath(os.path.normpath(os.path.join(base_path, path)))
        
        # Reject if path is outside base_path or allowed_roots
        if not PathUtils._is_allowed_path(resolved, base_path):
            raise exceptions.PlatformException(
                error='400',
                message='Path resolves outside allowed directory'
            )
        
        # Check if path must exist
        if must_exist and not os.path.exists(resolved):
            raise exceptions.PlatformException(
                error='404',
                message='Path does not exist: {}'.format(path)
            )
    
    @staticmethod
    def validate_paths(paths, base_path = None, must_exist: bool = False):
        """
        Validate file or directory paths against path traversal attacks.
        Accepts a list of paths and validates each one.
        Skips validation if path is None or not a string.
        Skips validation for URLs (http://, https://) and external paths (external://).
        
        :param paths: Path(s) to validate - can be str, Path, list of str/Path, or None
        :param base_path: Optional base directory to restrict path to (str or Path). If None, uses current working directory
        :param bool must_exist: If True, path must exist
        :raises PlatformException: If any path is invalid or contains traversal sequences
        """
        # Handle None - skip validation
        if paths is None:
            return
        
        # Convert base_path Path object to string
        if isinstance(base_path, Path):
            base_path = str(base_path)
        
        # Resolve base_path
        if base_path is None:
            base_path = os.getcwd()
        
        # Handle list of paths
        if isinstance(paths, list):
            for path in paths:
                PathUtils._validate_single_path(path, base_path, must_exist)
        else:
            # Single path
            PathUtils._validate_single_path(paths, base_path, must_exist)
    
    @staticmethod
    def validate_file_path(file_path, base_path = None, must_exist: bool = True):
        """
        Validate a file path against path traversal attacks.
        
        :param file_path: File path to validate (str or Path object)
        :param base_path: Optional base directory to restrict path to (str or Path). If None, uses current working directory
        :param bool must_exist: If True, file must exist (default: True)
        :raises PlatformException: If path is invalid, contains traversal sequences, or is not a file
        """
        # Convert Path objects to strings
        if isinstance(file_path, Path):
            file_path = str(file_path)
        if isinstance(base_path, Path):
            base_path = str(base_path)
        
        PathUtils.validate_paths(file_path, base_path=base_path, must_exist=must_exist)
        
        if must_exist and isinstance(file_path, str) and not file_path.startswith(('http://', 'https://', 'external://')):
            # Resolve path to check if it's a file
            if base_path is None:
                base_path = os.getcwd()
            if os.path.isabs(file_path):
                resolved = os.path.abspath(os.path.normpath(file_path))
            else:
                resolved = os.path.abspath(os.path.normpath(os.path.join(base_path, file_path)))
            
            if not os.path.isfile(resolved):
                raise exceptions.PlatformException(
                    error='400',
                    message='Path is not a file: {}'.format(file_path)
                )
    
    @staticmethod
    def validate_directory_path(dir_path, base_path = None, must_exist: bool = True):
        """
        Validate a directory path against path traversal attacks.
        
        :param dir_path: Directory path to validate (str or Path object)
        :param base_path: Optional base directory to restrict path to (str or Path). If None, uses current working directory
        :param bool must_exist: If True, directory must exist (default: True)
        :raises PlatformException: If path is invalid, contains traversal sequences, or is not a directory
        """
        # Convert Path objects to strings
        if isinstance(dir_path, Path):
            dir_path = str(dir_path)
        if isinstance(base_path, Path):
            base_path = str(base_path)
        
        PathUtils.validate_paths(dir_path, base_path=base_path, must_exist=must_exist)
        
        if must_exist and isinstance(dir_path, str) and not dir_path.startswith(('http://', 'https://', 'external://')):
            # Resolve path to check if it's a directory
            if base_path is None:
                base_path = os.getcwd()
            if os.path.isabs(dir_path):
                resolved = os.path.abspath(os.path.normpath(dir_path))
            else:
                resolved = os.path.abspath(os.path.normpath(os.path.join(base_path, dir_path)))
            
            if not os.path.isdir(resolved):
                raise exceptions.PlatformException(
                    error='400',
                    message='Path is not a directory: {}'.format(dir_path)
                )

