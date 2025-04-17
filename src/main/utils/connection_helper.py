import socket
import time
import logging

def wait_for_service(host, port, timeout=300, interval=5):
    """
    Wait for a network service to be available.
    
    Args:
        host (str): The hostname to connect to
        port (int): The port to connect to
        timeout (int): Maximum wait time in seconds
        interval (int): Interval between retries in seconds
        
    Returns:
        bool: True if connection successful, False if timed out
    """
    logging.info(f"Waiting for {host}:{port} to be available...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Try to resolve hostname first
            socket.gethostbyname(host)
            
            # Try to establish a connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                logging.info(f"Successfully connected to {host}:{port}")
                return True
            else:
                logging.warning(f"Cannot connect to {host}:{port} yet, retrying...")
        except socket.gaierror:
            logging.warning(f"Cannot resolve hostname {host}, retrying...")
        except Exception as e:
            logging.warning(f"Error checking {host}:{port}: {e}")
        
        time.sleep(interval)
    
    logging.error(f"Timed out waiting for {host}:{port} after {timeout} seconds")
    return False 