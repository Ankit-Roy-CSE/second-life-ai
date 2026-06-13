from fastapi import APIRouter

router = APIRouter()

# Routes implemented in P1-A1:
#   POST /auth/register
#   POST /auth/login
#   GET  /users/me
#   PUT  /users/me
#   GET  /users/candidates?category=&lat=&lng=  (cross-service read for Matching)
