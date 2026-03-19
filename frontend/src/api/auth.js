import client from './client'

export const login = (username, password) => {
  const form = new FormData()
  form.append('username', username)
  form.append('password', password)
  return client.post('/auth/login', form)
}

export const getMe = () =>
  client.get('/auth/me')
