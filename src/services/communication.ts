import { api } from './api'
import { Conversation, Message } from '../types'

export interface StartConversationPayload {
  participant_ids: number[]
  subject?: string
  property_id?: number
  initial_message?: string
}

export async function getConversations(): Promise<Conversation[]> {
  return api.request<Conversation[]>('/api/communications/conversations')
}

export async function startConversation(payload: StartConversationPayload): Promise<Conversation> {
  return api.request<Conversation>('/api/communications/conversations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function getConversationMessages(conversationId: number): Promise<Message[]> {
  return api.request<Message[]>(`/api/communications/conversations/${conversationId}/messages`)
}

export async function sendMessage(conversationId: number, body: string, attachmentUrl?: string): Promise<Message> {
  return api.request<Message>(`/api/communications/conversations/${conversationId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ body, attachment_url: attachmentUrl })
  })
}
