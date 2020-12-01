import asyncio
import websockets
import json

clientes = {}

async def mandar_mensagem(message):
  global clientes
  users_disconectados = []
  for user in clientes.keys():
    cliente = clientes.get(user)[0]
    try:
      await cliente.send(message)
    except:
      users_disconectados.append(user)

  for user in users_disconectados:
    clientes.pop(user)
  if len(users_disconectados) > 0:
    await listUsers()

async def receber_mensagem(websocket, path):
  async for m in websocket:
    mensagem = json.loads(m)
    if mensagem['type'] == 'signup':
      if not clientes.get(mensagem['user']):
        clientes[mensagem['user']] = [websocket, mensagem['userId']]
        await aceitar_username(mensagem['user'], mensagem['userId'])
        await listUsers()
      else:
        await rejeitar_username(websocket, mensagem['user'], mensagem['userId'])
    if mensagem['type'] == 'message':
      if mensagem['message'][0] == "~":
        user = mensagem['message'].split()[0][1:]
        print(user)
        await mensagem_privada(user, mensagem)
      elif clientes.get(mensagem['user']):
        await mandar_mensagem(m)

async def rejeitar_username(websocket, username,userId):
  rejeitar_mensagem = json.dumps({
    'type': 'reject',
    'user':username,
    'message':'Username já está em uso.',
    'userId':userId}
  )
  await websocket.send(rejeitar_mensagem)

async def aceitar_username(username,userId):
  aceitar_mensagem = json.dumps({
    'type': 'accepted',
    'user':username,
    'message':'Username aceito',
    'userId':userId}
  )
  await mandar_mensagem(aceitar_mensagem)

async def mensagem_privada(user,mensagem):
  global clientes
  if clientes.get(user):
    cliente = clientes.get(user)[0]
    mensagem_real = mensagem['message'].split()
    print(mensagem_real)
    mensagem_real = mensagem_real[1:]
    print(mensagem_real)
    mensagem['message'] = " ".join(mensagem_real)
    print("To:",user,"; Message: ", mensagem)
    try:
      await cliente.send(json.dumps(mensagem))
    except:
      clientes.pop(user)
      await listUsers()

async def listUsers():
  users = []
  for key in clientes.keys():
    users.append(key)
  users_mensagem = json.dumps({
    'type': 'users',
    'message': users
  })
  print("Sending:", users_mensagem)
  await mandar_mensagem(users_mensagem)


start_server = websockets.serve(receber_mensagem, "localhost", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()