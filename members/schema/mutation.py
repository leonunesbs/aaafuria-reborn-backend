import graphene
import requests
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from graphene_file_upload.scalars import Upload
from graphql import GraphQLError
from members.models import Member


class CreateAccount(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        name = graphene.String(required=True)
        nickname = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=True)
        rg = graphene.String(required=True)
        cpf = graphene.String(required=True)
        birth_date = graphene.String(required=True)
        group = graphene.String(required=True)
        avatar = Upload(required=True)

    ok = graphene.Boolean()
    member = graphene.Field('members.schema.nodes.MemberNode')

    def mutate(self, info, username, password, name, nickname, email, phone, rg, cpf, birth_date, group, avatar):
        if not (username or password or name or nickname or email or phone or rg or cpf or birth_date or group or avatar):
            raise GraphQLError(_('All fields are required'))

        if len(username) != 8:
            raise GraphQLError(_('Username must be 8 characters'))
        if len(password) != 6:
            raise GraphQLError(_('Password must be 6 characters'))
        if not username.isdigit():
            raise GraphQLError(_('Username must be numeric'))
        if not password.isdigit():
            raise GraphQLError(_('Password must be numeric'))

        member = Member.objects.create(
            registration=username,
            name=name,
            nickname=nickname,
            email=email,
            phone=phone,
            rg=rg,
            cpf=cpf,
            birth_date=birth_date,
            group=group,
            avatar=avatar,
            user=User.objects.create_user(
                username=username, password=password, email=email),
        )

        return CreateAccount(ok=True, member=member)


class CreateIntermedProfile(graphene.Mutation):
    class Arguments:
        nickname = graphene.String(required=True)
        avatar = Upload(required=True)
        vaccine_card = Upload(required=True)
        enroll = Upload(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            raise GraphQLError(_('Unauthenticated.'))

        member = info.context.user.member
        if not member.avatar:
            member.avatar = kwargs.get('avatar')
            member.save()

        vaccine_card, created = member.attachments.get_or_create(
            title='vaccine_card')
        vaccine_card.file = kwargs.get('vaccine_card')
        vaccine_card.save()

        enroll, created = member.attachments.get_or_create(title='enroll')
        enroll.file = kwargs.get('enroll')
        enroll.save()

        response = requests.post('http://intermednordeste.com/api/user',
                                 data={
                                     "name": member.name,
                                     "email": member.email,
                                     "nickname": kwargs.get('nickname'),
                                     "password": member.registration,
                                     "birth_date": member.birth_date.strftime('%Y-%m-%d'),
                                     "rg": member.rg,
                                     "cpf": member.cpf,
                                     "street": "Rua Vitorino Orthiges Fernandes",
                                     "number": "6123",
                                     "college": "UNINOVAFAPI",
                                     "course": "MEDICINA",
                                     "id_city": "3585",
                                     "id_state": "22",
                                     "id_type": "1",
                                     "phone": f'{member.phone[0:2]} {member.phone[2]} {member.phone[3:7]}-{member.phone[7:]}',
                                     "id_club": "9",
                                 }, files={
                                     "photo": member.avatar,
                                     "vaccine_card": vaccine_card.file,
                                     "enroll": enroll.file
                                 })

        if response.status_code != 201:
            raise GraphQLError(response.content)

        response = requests.post('http://intermednordeste.com/api/auth/login',
                                 data={
                                     "email": member.email,
                                     "password": member.registration
                                 })
        JWT = response.headers['authorization']

        if response.status_code != 201:
            raise GraphQLError(_('Error signing in INTERMED.'))

        response = requests.post('http://intermednordeste.com/api/event/registerTicket',
                                 data={
                                     "id_batch": 9,
                                 }, headers={
                                     "Authorization": f'Bearer {JWT}'})

        if response.status_code != 201:
            raise GraphQLError(_('Error registering in INTERMED.'))

        return CreateIntermedProfile(ok=True)


class Mutation(graphene.ObjectType):
    create_account = CreateAccount.Field()
    create_intermed_profile = CreateIntermedProfile.Field()
