from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
import config
from db import engine, Base, get_db
import models, schemas
from auth import get_password_hash, verify_password, create_access_token
from jose import jwt
from typing import List

app = FastAPI(title='MyTrello API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

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

def get_current_board(board_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = select(models.Board).where(
        models.Board.owner_id == current_user.id,
        models.Board.id == board_id
    )
    board = db.execute(query).scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail=f"Board with id {board_id} was not found")
    else:
        return board

def get_current_list(list_id: int, db: Session = Depends(get_db), current_board: models.Board = Depends(get_current_board)):
    query = select(models.BoardList).where(
        models.BoardList.board_id == current_board.id,
        models.BoardList.id == list_id
    )
    board_list = db.execute(query).scalar_one_or_none()
    if not board_list:
        raise HTTPException(status_code=404, detail=f"List with id {list_id} was not found")
    else:
        return board_list

def get_current_card(card_id: int, db: Session = Depends(get_db), current_list: models.BoardList = Depends(get_current_list)):
    query = select(models.Card).where(
        models.Card.list_id == current_list.id,
        models.Card.id == card_id
    )
    card = db.execute(query).scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card with id {card_id} was not found")
    else:
        return card



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

@app.patch('/boards/{board_id}', response_model=schemas.BoardOut, tags=['Board'])
def update_board(board_update: schemas.BoardCreate, db : Session = Depends(get_db), current_board: models.Board = Depends(get_current_board)):
    current_board.title = board_update.title
    db.commit()
    db.refresh(current_board)
    return current_board

@app.get('/boards', response_model=List[schemas.BoardOut], tags=['Board'])
def get_boards(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = select(models.Board).where(models.Board.owner_id == current_user.id)
    result = db.execute(query)
    boards = result.scalars().all()

    return boards

@app.delete('/boards/{board_id}', status_code=204, tags=['Board'])
def delete_board(db: Session = Depends(get_db), board: models.Board = Depends(get_current_board)):
    db.delete(board)
    db.commit()

    return Response(status_code=204)



@app.post('/boards/{board_id}/lists', response_model=schemas.ListOut, tags=['List'])
def create_list(lists: schemas.ListCreate, db: Session = Depends(get_db), board: models.Board = Depends(get_current_board)):
    new_list = models.BoardList(
        title = lists.title,
        board_id = board.id
    )

    db.add(new_list)
    db.commit()
    db.refresh(new_list)

    return new_list

@app.patch('/boards/{board_id}/lists/{list_id}', response_model=schemas.ListOut, tags=['List'])
def update_list(list_update: schemas.ListCreate, db: Session = Depends(get_db), current_list: models.BoardList = Depends(get_current_list)):
    current_list.title = list_update.title

    db.commit()
    db.refresh(current_list)
    return current_list

@app.get('/boards/{board_id}/lists/{list_id}', response_model=List[schemas.ListOut], tags=['List'])
def get_lists(db: Session = Depends(get_db), current_board: models.Board = Depends(get_current_board)):
    query = select(models.BoardList).where(models.BoardList.board_id == current_board.id)
    result = db.execute(query)
    boards = result.scalars().all()

    return boards

@app.delete('/boards/{board_id}/lists/{list_id}', status_code=204, tags=['List'])
def delete_list(db: Session = Depends(get_db), current_list: models.BoardList = Depends(get_current_list)):
    db.delete(current_list)
    db.commit()
    return Response(status_code=204)



@app.post('/boards/{board_id}/lists/{list_id}/cards', response_model=schemas.CardOut, tags=['Card'])
def create_card(card: schemas.CardCreate, db: Session = Depends(get_db), current_list: models.BoardList = Depends(get_current_list)):
    new_card = models.Card(
        title = card.title,
        description = card.description,
        list_id = current_list.id
    )

    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return new_card

@app.patch('/boards/{board_id}/lists/{list_id}/cards/{card_id}', response_model=schemas.CardOut, tags=['Card'])
def update_card(card_update: schemas.CardUpdate, db: Session = Depends(get_db), current_card: models.Card = Depends(get_current_card)):
    update = card_update.model_dump(exclude_unset=True)

    for key, value in update.items():
        setattr(current_card, key, value)

    db.commit()
    db.refresh(current_card)
    return current_card

@app.get('/boards/{board_id}/lists/{list_id}/cards', response_model=List[schemas.CardOut], tags=['Card'])
def get_cards(db: Session = Depends(get_db), current_list: models.BoardList = Depends(get_current_list)):
    query = select(models.Card).where(models.Card.list_id == current_list.id)
    result = db.execute(query)
    cards = result.scalars().all()

    return cards

@app.delete('/boards/{board_id}/lists/{list_id}/cards/{card_id}', status_code=204, tags=['Card'])
def delete_card(db: Session = Depends(get_db), current_card: models.Card = Depends(get_current_card)):
    db.delete(current_card)
    db.commit()
    return Response(status_code=204)