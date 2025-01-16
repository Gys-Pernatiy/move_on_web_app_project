type RequestBody = any | FormData

type RequestConfig = {
  method: 'POST' | 'GET' | 'PUT' | 'DELETE'
  data?: RequestBody
  isFileUpload?: boolean
}

async function fetchWithConfig<T>(
  url: string,
  { method, data, isFileUpload = false }: RequestConfig
): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: isFileUpload
      ? {}
      : {
          'Content-Type': 'application/json',
        },
    body: isFileUpload ? (data as FormData) : JSON.stringify(data),
    credentials: 'include',
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw new Error(errorData?.reason || `Ошибка: ${response.status}`)
  }

  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return await response.json()
  }

  return (await response.text()) as unknown as T
}

export default fetchWithConfig
