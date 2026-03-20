class DataBuilderError(Exception):
    """数据构建器基础异常"""
    pass


class SchemaError(DataBuilderError):
    """Schema 解析或验证错误"""
    pass


class StrategyError(DataBuilderError):
    """策略执行错误"""
    pass


class StrategyNotFoundError(StrategyError):
    """策略未找到"""
    pass


class FieldPathError(DataBuilderError):
    """字段路径解析错误"""
    pass
