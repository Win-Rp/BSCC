# BSCC Backend

V1 backend POC for the bid document duplicate checker.

## Stack

- FastAPI
- SQLite
- Local temporary file storage
- `python-docx` for `.docx`
- `pypdf` for text-based `.pdf`

## Run

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Notes

- This POC runs checking synchronously after upload so the frontend can integrate early.
- Multi-file detail access is locked until an order is marked as paid.
- Alipay is represented by a placeholder QR code URL in this stage.
