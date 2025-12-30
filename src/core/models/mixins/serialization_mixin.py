from datetime import datetime


class SerializationMixin:
    @staticmethod
    def is_des(descending, order):
        try:
            if descending:
                return order.desc()
            else:
                return order.asc()
        except Exception:
            return None

    @staticmethod
    def default_serializer(obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        except Exception:
            return None

    @staticmethod
    def to_dict(model):
        try:
            if isinstance(model, dict):
                return model
            elif hasattr(model, "__table__"):
                data = {
                    column.name: getattr(model, column.name)
                    for column in model.__table__.columns
                }
                data.pop("_sa_instance_state", None)
                return data
            else:
                raise TypeError("Unsupported type")
        except Exception:
            return None
