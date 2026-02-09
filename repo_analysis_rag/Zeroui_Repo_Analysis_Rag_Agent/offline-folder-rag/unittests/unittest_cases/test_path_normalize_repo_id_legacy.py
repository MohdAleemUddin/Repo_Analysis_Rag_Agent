import hashlib


def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def generate_repo_id(repo_path: str) -> str:
    normalized_path = normalize_path(repo_path)
    return hashlib.sha256(normalized_path.encode("utf-8")).hexdigest()


def test_repo_id_consistency():
    path_forward = "C:/Users/Project/Repo"
    path_backward = "C:\\Users\\Project\\Repo"
    assert generate_repo_id(path_forward) == generate_repo_id(path_backward)
import hashlib
import pytest


def normalize_path(path: str) -> str:
    # Normalize path by replacing backward slashes with forward slashes
    return path.replace("\\", "/")


def generate_repo_id(path: str) -> str:
    normalized_path = normalize_path(path)
    return hashlib.sha256(normalized_path.encode('utf-8')).hexdigest()


def test_repo_id_consistency():
    # Test for different slash directions
    path1 = "C:/Users/Project/Repo"
    path2 = "C:\\Users\\Project\\Repo"
    assert generate_repo_id(path1) == generate_repo_id(path2)
