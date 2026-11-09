# Belajar Python Part 19: Otorisasi & Role-Based Access Control di Flask

Kode pendamping tutorial **Belajar Python Part 19**, lanjutan dari Part 18 (Autentikasi dengan Flask-Login).

## Fitur

- Registrasi, login, logout (Flask-Login)
- Role `user`, `editor`, `admin`
- Decorator `roles_required(...)` untuk memproteksi route
- Halaman admin untuk mengubah role pengguna
- Pengecekan kepemilikan data (pemilik atau admin yang boleh edit postingan)
- Halaman error 403 kustom
- Perlindungan *open redirect* pada parameter `next`
- Perintah CLI `create-admin`
- 9 tes otomatis dengan pytest

## Menjalankan

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# buat akun admin pertama
flask --app app create-admin budi

# jalankan aplikasi
flask --app app run --debug
```

Buka http://127.0.0.1:5000

## Variabel lingkungan

| Variabel | Fungsi | Bawaan |
|---|---|---|
| `SECRET_KEY` | Kunci sesi, **wajib diganti** di production | `dev-ganti-di-production` |
| `DATABASE_URL` | URL database SQLAlchemy | `sqlite:///app.db` |

## Menjalankan tes

```bash
pytest
```

## Struktur

```
├── app.py            # application factory, route, CLI
├── models.py         # User, Post, konstanta role
├── decorators.py     # roles_required
├── templates/        # Jinja templates (+ errors/403.html)
└── tests/test_access.py
```

## Catatan

Jika database dari Part 18 sudah ada, kolom `role` belum ada di tabel lama. Hapus `instance/app.db` untuk latihan, atau tunggu Part 20 (Flask-Migrate) untuk cara migrasi yang benar.
