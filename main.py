from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from db import engine, Base, get_db
import models, schemas
from auth import get_password_hash

app = FastAPI(title='MyTrello API')
Base.metadata.create_all(bind=engine)

@app.post('/users/', response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
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