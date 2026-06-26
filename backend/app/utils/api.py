from fastapi import HTTPException


def ok(data=None) -> dict:
    return {"success": True, "data": data if data is not None else {}, "error": None}


def fail(code: str, message: str, status_code: int = 400) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"success": False, "data": None, "error": {"code": code, "message": message}},
    )
