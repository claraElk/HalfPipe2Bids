#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main module for the project
"""

import os
import logging
from src.preprocessor import Preprocessor

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s [%(levelname)s] %(message)s',
)

def main():
    """
    Main function to run the project
    """
    try: 
        preprocessor = Preprocessor()
        preprocessor.run()
    
    except FileExistsError as e:
        logging.critical("Error while retrieving HalfPipe data: %s", e)
    except FileNotFoundError as e:
        logging.critical("Error while retrieving HalfPipe data: %s", e)
    except PermissionError as e:
        logging.critical("Error while retrieving HalfPipe data: %s", e)
    except ValueError as e:
        logging.critical(e)
    except Exception as e:
        logging.critical("An unexpected error occurred: %s", e)

if __name__ == "__main__":
    main()