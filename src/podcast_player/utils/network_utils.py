"""
Network utility functions for the Podcast Player application.

This module provides network-related utilities including connection testing,
URL validation, and download helpers.
"""

import socket
import urllib.request
import urllib.error
from urllib.parse import urlparse, urljoin
from typing import Optional, Tuple, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import urllib3


class NetworkUtils:
    """Utility class for network operations."""
    
    # Default timeout values
    DEFAULT_TIMEOUT = 30
    CONNECTION_TIMEOUT = 10
    
    @staticmethod
    def is_internet_available(test_url: str = "http://www.google.com", timeout: int = CONNECTION_TIMEOUT) -> bool:
        """
        Check if internet connection is available.
        
        Args:
            test_url: URL to test connection with
            timeout: Connection timeout in seconds
            
        Returns:
            True if internet is available, False otherwise
        """
        try:
            response = urllib.request.urlopen(test_url, timeout=timeout)
            return response.getcode() == 200
        except (urllib.error.URLError, socket.timeout):
            return False
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Validate if a string is a valid URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def is_valid_rss_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[bool, Optional[str]]:
        """
        Check if a URL is a valid RSS feed.
        
        Args:
            url: URL to check
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not NetworkUtils.is_valid_url(url):
            return False, "Invalid URL format"
        
        try:
            session = NetworkUtils.create_session()
            response = session.head(url, timeout=timeout, allow_redirects=True)
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"
            
            content_type = response.headers.get('content-type', '').lower()
            
            # Check for RSS/XML content types
            valid_types = [
                'application/rss+xml',
                'application/xml',
                'text/xml',
                'application/atom+xml'
            ]
            
            if any(valid_type in content_type for valid_type in valid_types):
                return True, None
            
            # Some feeds might not have proper content-type, try a GET request
            response = session.get(url, timeout=timeout, stream=True)
            
            # Read first few bytes to check for XML
            chunk = response.raw.read(1024).decode('utf-8', errors='ignore')
            if '<?xml' in chunk or '<rss' in chunk or '<feed' in chunk:
                return True, None
            
            return False, "Not an RSS/XML feed"
            
        except requests.exceptions.RequestException as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    @staticmethod
    def create_session(max_retries: int = 3) -> requests.Session:
        """
        Create a requests session with retry strategy.
        
        Args:
            max_retries: Maximum number of retries
            
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Define retry strategy with compatibility for different urllib3 versions
        # Check urllib3 version to use correct parameter names
        urllib3_version = tuple(map(int, urllib3.__version__.split('.')[:2]))
        
        retry_kwargs = {
            'total': max_retries,
            'backoff_factor': 1
        }
        
        # Use appropriate parameter names based on urllib3 version
        if urllib3_version >= (1, 26):
            # New parameter names (urllib3 >= 1.26)
            retry_kwargs.update({
                'allowed_methods': ["HEAD", "GET", "OPTIONS"],
                'status_forcelist': [429, 500, 502, 503, 504]
            })
        else:
            # Old parameter names (urllib3 < 1.26)
            retry_kwargs.update({
                'method_whitelist': ["HEAD", "GET", "OPTIONS"],
                'status_forcelist': [429, 500, 502, 503, 504]
            })
        
        retry_strategy = Retry(**retry_kwargs)
        
        # Create adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        # Mount adapter for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': 'Podcast Player/1.0.0 (RSS Reader)',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        return session
    
    @staticmethod
    def download_with_progress(url: str, progress_callback=None, timeout: int = DEFAULT_TIMEOUT) -> Optional[bytes]:
        """
        Download content from URL with progress tracking.
        
        Args:
            url: URL to download from
            progress_callback: Function to call with progress updates (received, total)
            timeout: Request timeout in seconds
            
        Returns:
            Downloaded content as bytes, or None if download failed
        """
        try:
            session = NetworkUtils.create_session()
            
            with session.get(url, timeout=timeout, stream=True) as response:
                response.raise_for_status()
                
                # Get total size if available
                total_size = response.headers.get('content-length')
                total_size = int(total_size) if total_size else None
                
                content = b''
                downloaded = 0
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        content += chunk
                        downloaded += len(chunk)
                        
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(downloaded, total_size)
                
                return content
                
        except requests.exceptions.RequestException as e:
            print(f"Download error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected download error: {e}")
            return None
    
    @staticmethod
    def get_url_info(url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
        """
        Get information about a URL without downloading full content.
        
        Args:
            url: URL to get information about
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with URL information
        """
        info = {
            'url': url,
            'accessible': False,
            'status_code': None,
            'content_type': None,
            'content_length': None,
            'final_url': None,
            'error': None
        }
        
        try:
            session = NetworkUtils.create_session()
            response = session.head(url, timeout=timeout, allow_redirects=True)
            
            info.update({
                'accessible': True,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type'),
                'content_length': response.headers.get('content-length'),
                'final_url': response.url
            })
            
            # Convert content length to int if available
            if info['content_length']:
                try:
                    info['content_length'] = int(info['content_length'])
                except ValueError:
                    info['content_length'] = None
            
        except requests.exceptions.RequestException as e:
            info['error'] = str(e)
        except Exception as e:
            info['error'] = f"Unexpected error: {str(e)}"
        
        return info
    
    @staticmethod
    def resolve_url(base_url: str, relative_url: str) -> str:
        """
        Resolve a relative URL against a base URL.
        
        Args:
            base_url: Base URL
            relative_url: Relative URL to resolve
            
        Returns:
            Absolute URL
        """
        try:
            return urljoin(base_url, relative_url)
        except Exception:
            return relative_url
    
    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """
        Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name, or None if extraction failed
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return None
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize a URL by ensuring proper format.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        if not url:
            return ""
        
        url = url.strip()
        
        # Add http:// if no scheme is present
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        return url
    
    @staticmethod
    def is_local_url(url: str) -> bool:
        """
        Check if URL is a local/localhost URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is local, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            return any([
                domain.startswith('localhost'),
                domain.startswith('127.'),
                domain.startswith('192.168.'),
                domain.startswith('10.'),
                domain.startswith('172.'),
                domain == ''
            ])
        except Exception:
            return False