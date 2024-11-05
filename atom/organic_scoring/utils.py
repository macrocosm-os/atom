def is_overridden(method) -> bool:
    """Determine if the method is overridden in the derived class.

    Args:
        method: The method to check.

    Returns:
        bool: True if the method is overridden in the derived class, False otherwise.
    """
    child_instance = method.__self__
    method_name = method.__name__
    child_class = child_instance.__class__
    
    # Find the base class that defines the method.
    for base_class in child_class.__bases__:
        if hasattr(base_class, method_name):
            base_method = getattr(base_class, method_name)
            return method.__qualname__ != base_method.__qualname__

    return False
