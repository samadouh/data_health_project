import paramiko
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class SSHClient:
    def __init__(self, host, username, port=22):
        self.host = host
        self.username = username
        self.port = port
        self.client = None 
        logger.debug(f"Initialized SSHClient for {self.host} with user {self.username} and port {self.port}")

    def connect(self):
        """
        Create the SSH client and set the missing host key policy.
        Assumung that public key is deployed.
        """
        logger.info(f"Attempting to connect to {self.host} on port {self.port}")
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
        
        try:
            self.client.connect(self.host, username=self.username, port=self.port)
            logger.info(f"Successfully connected to {self.host}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}: {str(e)}")
            raise Exception(f"Failed to connect: {str(e)}")

    def is_connected(self):
        """
        Check that connection still active.
        """
        try:
            transport = self.client.get_transport()
            is_active = transport and transport.is_active()
            logger.debug(f"Connection active: {is_active}")
            return is_active
        except Exception as e:
            logger.error(f"Error checking connection: {str(e)}")
            return False

    def exec_command(self, cmd):
        """
        execute command on remote Linux and return stdout and stderr
        """
        if self.is_connected():
            logger.debug(f"Executing command: {cmd}")
            
            # Execute the cmd and get stdin, stdout, stderr
            stdin, stdout, stderr = self.client.exec_command(cmd)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if error:
                logger.error(f"Command execution failed: {error}")
            else:
                logger.info(f"Command executed successfully: {cmd}")
            
            return output, error
        else:
            logger.error("SSH connection is not active")
            raise Exception("SSH connection is not active")

    def copy_file_from_remote(self, remote_path, local_path):
        """
        Copy a file from a remote Linux machine using SFTP.
        """
        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            logging.info(f"Successfully copied {remote_path} to {local_path}")
        except Exception as e:
            logging.error(f"Error copying file via SFTP: {e}")
            raise

    def close(self):
        """
        Close connection to remote Linux
        """
        if self.client:
            self.client.close()
            logger.info(f"SSH connection to {self.host} closed")
