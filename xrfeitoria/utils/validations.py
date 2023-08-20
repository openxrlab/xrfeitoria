class Validator:
    @classmethod
    def validate_argument_type(cls, value, typelist: list[type]):
        if not isinstance(typelist, list):
            typelist = [typelist]
        if any([isinstance(value, tp) for tp in typelist]):
            return
        raise TypeError(
            f"Invalid argument type, expected {[tp.__name__ for tp in typelist]} (got {value.__class__.__name__} instead)."
        )

    @classmethod
    def validate_vector(cls, value, length: int):
        cls.validate_argument_type(value=value, typelist=[list, tuple])
        if len(value) != length:
            raise ValueError(f"Invalid vector length, expected 3 (got {len(value)} instead).")
        for val in value:
            if not isinstance(val, float) and not isinstance(val, int):
                raise TypeError(
                    f"Invalid argument type, expected 'float' vector or 'int' vector (got '{val.__class__.__name__}' in vector instead)."
                )
