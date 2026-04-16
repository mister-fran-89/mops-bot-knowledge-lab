'use client'

import ChatInput from './ChatInput'
import MessageArea from './MessageArea'
import Icon from '@/components/ui/icon'

const ChatArea = ({ onMobileMenuOpen }: { onMobileMenuOpen?: () => void }) => {
  return (
    <main className="relative flex flex-grow flex-col bg-background min-w-0 md:m-1.5 md:rounded-xl">
      <div className="mobile-header flex items-center px-4 pt-2 md:hidden">
        <button
          onClick={onMobileMenuOpen}
          className="p-2 text-primary"
          aria-label="Open menu"
        >
          <Icon type="sheet" size="xs" />
        </button>
      </div>
      <MessageArea />
      {/* Mobile: fixed bottom bar so iOS always renders it in the tap zone */}
      <div className="fixed bottom-0 left-0 right-0 z-30 bg-background chat-input-area md:hidden">
        <ChatInput />
      </div>
      {/* Desktop: sticky as before */}
      <div className="hidden md:block sticky bottom-0 ml-9 px-4 pb-2">
        <ChatInput />
      </div>
    </main>
  )
}

export default ChatArea
