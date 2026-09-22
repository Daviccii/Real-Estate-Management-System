import React, { useEffect, useState } from 'react'
import { getConversations, getConversationMessages, sendMessage, startConversation } from '../../services/communication'
import { Conversation, Message } from '../../types'
import { useAuth } from '../../contexts/AuthContext'

export const TenantMessages: React.FC = () => {
  const { user } = useAuth()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConv, setSelectedConv] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMsg, setNewMsg] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [showNewModal, setShowNewModal] = useState(false)
  const [newSubject, setNewSubject] = useState('')
  const [initialText, setInitialText] = useState('')

  const loadConversations = () => {
    getConversations()
      .then((convs) => {
        setConversations(convs)
        if (convs.length > 0 && !selectedConv) {
          setSelectedConv(convs[0])
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    if (selectedConv) {
      getConversationMessages(selectedConv.id).then(setMessages)
    }
  }, [selectedConv])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedConv || !newMsg.trim()) return
    setSending(true)
    try {
      const msg = await sendMessage(selectedConv.id, newMsg)
      setMessages((prev) => [...prev, msg])
      setNewMsg('')
    } catch (err: any) {
      alert(err.message || 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  const handleStartConversation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSubject.trim()) return
    try {
      const conv = await startConversation({
        participant_ids: [],
        subject: newSubject,
        initial_message: initialText || undefined,
      })
      setShowNewModal(false)
      setNewSubject('')
      setInitialText('')
      setConversations((prev) => [conv, ...prev])
      setSelectedConv(conv)
    } catch (err: any) {
      alert(err.message || 'Failed to create conversation')
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading your inbox...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Messages & Inquiries</h1>
          <p className="text-slate-500 text-sm mt-1">Direct communication with your landlord, property manager, and service providers.</p>
        </div>
        <button
          onClick={() => setShowNewModal(true)}
          className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-sm font-medium transition shadow-sm"
        >
          + New Message
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm grid grid-cols-1 md:grid-cols-3 min-h-[500px] overflow-hidden">
        {/* Conversations List */}
        <div className="border-r border-slate-100 p-4 divide-y divide-slate-50">
          <div className="font-semibold text-xs text-slate-400 uppercase tracking-wider mb-3 px-2">Conversations</div>
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-400">No active threads. Start a new message to get in touch.</div>
          ) : (
            conversations.map((c) => (
              <button
                key={c.id}
                onClick={() => setSelectedConv(c)}
                className={`w-full text-left p-3 rounded-xl transition ${
                  selectedConv?.id === c.id ? 'bg-teal-50 text-teal-900 font-medium' : 'hover:bg-slate-50 text-slate-700'
                }`}
              >
                <div className="font-semibold text-sm truncate">{c.subject || `Thread #${c.id}`}</div>
                <div className="text-xs text-slate-400 mt-1 truncate">
                  {c.last_message || 'No messages yet'}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Active Conversation Messages */}
        <div className="md:col-span-2 flex flex-col justify-between p-6">
          {selectedConv ? (
            <>
              <div>
                <div className="pb-4 border-b border-slate-100 flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-base text-slate-800">{selectedConv.subject || 'Direct Message'}</h3>
                    <span className="text-xs text-slate-400">Thread ID: #{selectedConv.id}</span>
                  </div>
                </div>

                <div className="py-4 space-y-3 max-h-[350px] overflow-y-auto pr-2">
                  {messages.length === 0 ? (
                    <div className="py-8 text-center text-xs text-slate-400">No messages in this thread yet. Send a message below.</div>
                  ) : (
                    messages.map((m) => {
                      const isMe = m.sender_id === user?.id
                      return (
                        <div key={m.id} className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}>
                          <div
                            className={`max-w-md p-3.5 rounded-2xl text-sm ${
                              isMe
                                ? 'bg-teal-700 text-white rounded-br-none'
                                : 'bg-slate-100 text-slate-800 rounded-bl-none'
                            }`}
                          >
                            <p className="leading-relaxed">{m.body}</p>
                          </div>
                          <span className="text-[10px] text-slate-400 mt-1 px-1">
                            {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      )
                    })
                  )}
                </div>
              </div>

              <form onSubmit={handleSend} className="pt-4 border-t border-slate-100 flex gap-2">
                <input
                  type="text"
                  placeholder="Type your message here..."
                  value={newMsg}
                  onChange={(e) => setNewMsg(e.target.value)}
                  className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
                <button
                  type="submit"
                  disabled={sending || !newMsg.trim()}
                  className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl transition disabled:opacity-50"
                >
                  {sending ? 'Sending...' : 'Send'}
                </button>
              </form>
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-center text-slate-400 text-sm">
              Select a conversation thread or start a new message.
            </div>
          )}
        </div>
      </div>

      {/* New Conversation Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-100">
              <h3 className="font-bold text-lg text-slate-800">Start New Message Thread</h3>
              <button onClick={() => setShowNewModal(false)} className="text-slate-400 hover:text-slate-600 font-bold text-xl">
                &times;
              </button>
            </div>
            <form onSubmit={handleStartConversation} className="py-4 space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Subject *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Lease Renewal Inquiry / Parking Query"
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Message</label>
                <textarea
                  rows={3}
                  placeholder="Write your initial message..."
                  value={initialText}
                  onChange={(e) => setInitialText(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>
              <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-semibold shadow transition"
                >
                  Start Conversation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
export default TenantMessages
