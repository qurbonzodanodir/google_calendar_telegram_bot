def test_finlivo_external_import():
    """
    Verifies that we can import modules from the external FinLivo project.
    """
    try:
        import main
        assert main is not None
        print("   ✅ Successfully imported 'main' from FinLivo.")
    except ImportError as e:
        pytest.fail(f"Could not import module from external project: {e}")

