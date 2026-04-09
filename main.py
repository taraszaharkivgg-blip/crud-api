from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
import config
from db import engine, Base, get_db
import models, schemas
from auth import get_password_hash, verify_password, create_access_token
from jose import jwt
from typing import List

app = FastAPI(title='MyTrello API')
Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.settings.SECRET_KEY, algorithms=[config.settings.ALGORITHM])
        user_id = payload.get('user_id')
        if user_id is None:
            raise credentials_exception

    except:
        raise credentials_exception

    query = select(models.User).where(models.User.id == user_id)
    user = db.execute(query).scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user

@app.post('/auth/register', response_model=schemas.UserOut, tags=['Authorization'])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    #db_user = db.query(models.User).filter(models.User.email == user.email).first()
    query = select(models.User).where(models.User.email == user.email)
    db_user = db.execute(query).scalar_one_or_none()

    print(f"DEBUG: password type is {type(user.password)}, value is {user.password}")
    if db_user:
        raise HTTPException(status_code=400, detail='This email is already taken')

    hashed_pwd = get_password_hash(user.password)

    new_user = models.User(
        email = user.email,
        hashed_password = hashed_pwd,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post('/auth/login', tags=['Authorization'])
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    query = select(models.User).where(models.User.email == user_credentials.username)
    user = db.execute(query).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=403, detail='Invalid Email or Password')

    if not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=403, detail='Invalid Email or Password')

    access_token = create_access_token(data={'user_id': user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post('/boards', response_model=schemas.BoardOut, tags=['Board'])
def create_board(board: schemas.BoardCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_board = models.Board(
        title = board.title,
        owner_id = current_user.id
    )

    db.add(new_board)
    db.commit()
    db.refresh(new_board)

    return new_board

@app.get('/boards', response_model=List[schemas.BoardOut], tags=['Board'])
def get_board(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = select(models.Board).where(models.Board.owner_id == current_user.id)
    result = db.execute(query)
    boards = result.scalars().all()

    return boards
