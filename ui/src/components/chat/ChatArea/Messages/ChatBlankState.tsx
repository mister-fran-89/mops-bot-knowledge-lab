'use client'

import { motion } from 'framer-motion'
import { useStore } from '@/store'
import { useQueryState } from 'nuqs'

const ChatBlankState = () => {
  const { agents } = useStore()
  const [agentId] = useQueryState('agent')

  const agent = agents.find((a) => a.id === agentId)

  return (
    <section
      className="flex flex-col items-center text-center font-geist"
      aria-label="Welcome message"
    >
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="flex max-w-xl flex-col gap-y-4"
      >
        <h1 className="text-3xl font-semibold tracking-tight">
          {agent?.name || 'MOPS Knowledge Lab'}
        </h1>
        <p className="text-sm text-primary/50">
          {agent?.description || 'Select an agent to get started.'}
        </p>
      </motion.div>
    </section>
  )
}

export default ChatBlankState
