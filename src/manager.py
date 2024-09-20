#Bismillahirrahmanirrahim

from enum import Enum

class Manager(Enum):
    URL = "https://ninova.itu.edu.tr" #With enum, anyone can change the URL. It will arrise "AttributeError: Cannot reassign members."

