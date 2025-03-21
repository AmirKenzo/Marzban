from app.db.models import Admin
from app.operation import BaseOperator
from app.models.user_template import UserTemplateCreate, UserTemplateModify, UserTemplateResponse
from app.db import Session, crud
from sqlalchemy.exc import IntegrityError
from app.utils.logger import get_logger

logger = get_logger("user-template-operator")


class UserTemplateOperation(BaseOperator):
    async def add_user_template(
        self, db: Session, new_user_template: UserTemplateCreate, admin: Admin
    ) -> UserTemplateResponse:
        for group_id in new_user_template.group_ids:
            await self.get_validated_group(db, group_id)
        try:
            user_template = crud.create_user_template(db, new_user_template)
            logger.info(f'User template "{user_template.name}" created by admin "{admin.username}"')
            return user_template
        except IntegrityError:
            db.rollback()
            self.raise_error("Template by this name already exists", 409)

    async def modify_user_template(
        self, db: Session, template_id: int, modify_user_template: UserTemplateModify, admin: Admin
    ) -> UserTemplateResponse:
        dbuser_template = await self.get_validated_user_template(db, template_id)
        if modify_user_template.group_ids:
            for group_id in modify_user_template.group_ids:
                await self.get_validated_group(db, group_id)
        try:
            user_template = crud.update_user_template(db, dbuser_template, modify_user_template)
            logger.info(f'User template "{user_template.name}" modified by admin "{admin.username}"')
            return user_template
        except IntegrityError:
            db.rollback()
            self.raise_error("Template by this name already exists", 409)

    async def remove_user_template(self, db: Session, template_id: int, admin: Admin) -> None:
        dbuser_template = await self.get_validated_user_template(db, template_id)
        crud.remove_user_template(db, dbuser_template)
        logger.info(f'User template "{dbuser_template.name}" deleted by admin "{admin.username}"')

    async def get_user_templates(self, db: Session, offset: int, limit: int) -> list[UserTemplateResponse]:
        return crud.get_user_templates(db, offset, limit)
