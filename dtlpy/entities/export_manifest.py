"""
Export Manifest Entity for V3 LanceDB Export
"""
import gzip
import json
import logging
import os
from typing import Generator, List, Optional

from .base_entity import DlEntity, DlProperty

logger = logging.getLogger(name='dtlpy')


class ExportPartition(DlEntity):
    """
    Represents a partition in the V3 LanceDB export manifest.
    
    Each partition contains a subset of exported items in NDJSON format.
    """
    index = DlProperty(location=['index'], _type=int, default=0)
    hash = DlProperty(location=['hash'], _type=str, default='')
    item_count = DlProperty(location=['itemCount'], _type=int, default=0)
    file_path = DlProperty(location=['filePath'], _type=str, default='')
    file_size = DlProperty(location=['fileSize'], _type=int, default=0)
    url = DlProperty(location=['url'], _type=str, default='')

    @classmethod
    def from_json(cls, _json: dict) -> 'ExportPartition':
        """
        Build an ExportPartition entity from JSON
        
        :param dict _json: JSON dictionary from API response
        :return: ExportPartition object
        """
        return cls(_dict=_json)

    def to_json(self) -> dict:
        """
        Returns JSON format of object
        
        :return: dict
        """
        return self._dict.copy()


class ExportFile(DlEntity):
    """
    Represents a file entry in the V3 LanceDB export manifest.
    """
    size = DlProperty(location=['size'], _type=int, default=0)
    format = DlProperty(location=['format'], _type=str, default='unknown')
    compression = DlProperty(location=['compression'], _type=str, default='gzip')
    url = DlProperty(location=['url'], _type=str, default='')
    checksum = DlProperty(location=['checksum'], _type=str, default='')
    filename = DlProperty(location=['filename'], _type=str, default='')
    path = DlProperty(location=['path'], _type=str, default='')

    @classmethod
    def from_json(cls, _json: dict) -> 'ExportFile':
        """
        Build an ExportFile entity from JSON
        
        :param dict _json: JSON dictionary from API response
        :return: ExportFile object
        """
        return cls(_dict=_json)

    def to_json(self) -> dict:
        """
        Returns JSON format of object
        
        :return: dict
        """
        return self._dict.copy()


class ExportStatistics(DlEntity):
    """
    Statistics for the V3 LanceDB export.
    """
    total_records = DlProperty(location=['totalRecords'], _type=int, default=0)
    total_bytes = DlProperty(location=['totalBytes'], _type=int, default=0)
    file_count = DlProperty(location=['fileCount'], _type=int, default=0)
    processing_time_ms = DlProperty(location=['processingTimeMs'], _type=int, default=0)

    @classmethod
    def from_json(cls, _json: dict) -> 'ExportStatistics':
        """
        Build an ExportStatistics entity from JSON
        
        :param dict _json: JSON dictionary from API response
        :return: ExportStatistics object
        """
        return cls(_dict=_json)

    def to_json(self) -> dict:
        """
        Returns JSON format of object
        
        :return: dict
        """
        return self._dict.copy()


class ExportManifest(DlEntity):
    """
    Represents the manifest returned by the V3 LanceDB export API.
    
    The manifest contains metadata about the export including:
    - Export and dataset identifiers
    - Partition information for parallel downloads
    - File list with checksums for integrity verification
    - Statistics about the export operation
    """
    manifest_version = DlProperty(location=['manifestVersion'], _type=str, default='1.0')
    export_id = DlProperty(location=['exportId'], _type=str, default='')
    dataset_id = DlProperty(location=['datasetId'], _type=str, default='')
    exported_at = DlProperty(location=['exportedAt'], _type=str, default='')
    format = DlProperty(location=['format'], _type=str, default='ndjson')
    version = DlProperty(location=['version'], default=dict)
    filters = DlProperty(location=['filters'], default=dict)
    metadata = DlProperty(location=['metadata'], default=dict)
    
    # Partitioning info
    partition_count = DlProperty(location=['partitioning', 'partitionCount'], _type=int, default=0)
    
    # Version tracking for diff exports
    from_version = DlProperty(location=['fromVersion'], _type=int, default=None)
    to_version = DlProperty(location=['toVersion'], _type=int, default=None)
    mode = DlProperty(location=['mode'], _type=str, default='full')
    
    # Local paths after download
    local_path = DlProperty(location=['localPath'], _type=str, default=None)

    def __init__(self, _dict=None, **kwargs):
        super().__init__(_dict=_dict, **kwargs)
        self._partitions: Optional[List[ExportPartition]] = None
        self._files: Optional[List[ExportFile]] = None
        self._statistics: Optional[ExportStatistics] = None
        self._downloaded_files: List[str] = []

    @property
    def partitions(self) -> List[ExportPartition]:
        """List of export partitions"""
        if self._partitions is None:
            partitioning = self._dict.get('partitioning', {})
            self._partitions = [
                ExportPartition.from_json(p) 
                for p in partitioning.get('partitions', [])
            ]
        return self._partitions

    @property
    def files(self) -> List[ExportFile]:
        """List of export files"""
        if self._files is None:
            self._files = [
                ExportFile.from_json(f) 
                for f in self._dict.get('files', [])
            ]
        return self._files

    @property
    def statistics(self) -> ExportStatistics:
        """Export statistics"""
        if self._statistics is None:
            self._statistics = ExportStatistics.from_json(
                self._dict.get('statistics', {})
            )
        return self._statistics

    @property
    def downloaded_files(self) -> List[str]:
        """List of local file paths after download"""
        return self._downloaded_files
    
    @downloaded_files.setter
    def downloaded_files(self, value: List[str]):
        self._downloaded_files = value

    @property
    def total_records(self) -> int:
        """Total number of records in the export"""
        return self.statistics.total_records

    @property
    def total_bytes(self) -> int:
        """Total size of exported data in bytes"""
        return self.statistics.total_bytes

    @classmethod
    def from_json(cls, _json: dict, export_result: dict = None) -> 'ExportManifest':
        """
        Build an ExportManifest entity from JSON
        
        :param dict _json: JSON dictionary from manifest API response
        :param dict export_result: Optional export result from command spec
        :return: ExportManifest object
        """
        _dict = _json.copy()
        
        # Merge export result info if available
        if export_result:
            _dict['fromVersion'] = export_result.get('fromVersion')
            _dict['toVersion'] = export_result.get('toVersion')
            _dict['mode'] = export_result.get('mode', 'full')
        
        return cls(_dict=_dict)

    def to_json(self) -> dict:
        """
        Returns JSON format of object
        
        :return: dict
        """
        return self._dict.copy()

    def get_partition_urls(self) -> List[str]:
        """
        Get list of direct download URLs for all partitions
        
        :return: List of signed URLs
        """
        return [p.url for p in self.partitions]

    def get_file_paths(self) -> List[str]:
        """
        Get list of proxy paths for all files (requires JWT auth)
        
        :return: List of file paths
        """
        return [f.path for f in self.files]

    def decompress(self, output_path: str = None) -> List[str]:
        """
        Decompress all downloaded .gz partition files.
        
        :param str output_path: Directory to write decompressed files. Defaults to same directory as downloaded files.
        :return: List of paths to decompressed NDJSON files
        """
        if not self._downloaded_files:
            raise ValueError("No downloaded files to decompress. Run export with download first.")

        decompressed = []
        for gz_path in self._downloaded_files:
            if not gz_path.endswith('.gz'):
                decompressed.append(gz_path)
                continue

            out_path = gz_path[:-3]  # strip .gz
            if output_path is not None:
                os.makedirs(output_path, exist_ok=True)
                out_path = os.path.join(output_path, os.path.basename(out_path))

            with gzip.open(gz_path, 'rb') as f_in, open(out_path, 'wb') as f_out:
                while True:
                    chunk = f_in.read(8192)
                    if not chunk:
                        break
                    f_out.write(chunk)

            decompressed.append(out_path)
            logger.debug(f"Decompressed {gz_path} -> {out_path}")

        return sorted(decompressed)

    def iter_records(self) -> Generator[dict, None, None]:
        """
        Iterate over all exported records across all downloaded partition files.
        
        Handles gzip decompression transparently. Each yielded dict is one
        NDJSON record representing an exported item.
        
        :return: Generator yielding parsed JSON records
        """
        if not self._downloaded_files:
            raise ValueError("No downloaded files to read. Run export with download first.")

        for file_path in sorted(self._downloaded_files):
            opener = gzip.open if file_path.endswith('.gz') else open
            with opener(file_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield json.loads(line)
