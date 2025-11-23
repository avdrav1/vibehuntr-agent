/**
 * Welcome Component
 * 
 * Displays a welcome screen when no messages are present.
 * Shows Vibehuntr branding and agent capabilities.
 * 
 * Requirements:
 * - 9.1: Display Vibehuntr logo and colors
 * - 9.4: Use dark theme with glassmorphism effects
 */

interface WelcomeProps {
  className?: string;
}

export function Welcome({ className = '' }: WelcomeProps) {
  const capabilities = [
    {
      icon: '👥',
      title: 'Create Profiles & Groups',
      description: 'Set up your profile and form groups with friends'
    },
    {
      icon: '📅',
      title: 'Find Meeting Times',
      description: 'Discover optimal times when everyone is available'
    },
    {
      icon: '🎉',
      title: 'Plan Events',
      description: 'Organize activities and get personalized suggestions'
    },
    {
      icon: '📍',
      title: 'Discover Places',
      description: 'Find restaurants, venues, and activities nearby'
    },
    {
      icon: '💬',
      title: 'Share Feedback',
      description: 'Rate events and help improve future recommendations'
    }
  ];

  return (
    <div 
      className={`flex-1 flex items-center justify-center p-8 ${className}`}
      role="status"
      aria-live="polite"
    >
      <div className="text-center max-w-3xl">
        {/* Logo and Title */}
        <div className="mb-8">
          <div 
            className="text-7xl mb-4 animate-bounce-slow" 
            role="img" 
            aria-label="Vibehuntr logo"
          >
            🎉
          </div>
          <h1 
            className="text-4xl font-bold mb-3 text-gradient"
            style={{ fontFamily: 'var(--font-family)' }}
          >
            Welcome to Vibehuntr
          </h1>
          <p 
            className="text-lg mb-2"
            style={{ color: 'var(--color-text)' }}
          >
            Your AI-powered event planning assistant
          </p>
          <p 
            className="text-sm"
            style={{ color: 'var(--color-text-muted)' }}
          >
            Start a conversation to get personalized recommendations!
          </p>
        </div>

        {/* Capabilities Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
          {capabilities.map((capability, index) => (
            <div
              key={index}
              className="glass p-4 rounded-lg hover:scale-105 transition-transform duration-200"
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <div className="text-3xl mb-2" role="img" aria-label={capability.title}>
                {capability.icon}
              </div>
              <h3 
                className="text-sm font-semibold mb-1"
                style={{ 
                  color: 'var(--color-text)',
                  fontFamily: 'var(--font-family)'
                }}
              >
                {capability.title}
              </h3>
              <p 
                className="text-xs"
                style={{ color: 'var(--color-text-muted)' }}
              >
                {capability.description}
              </p>
            </div>
          ))}
        </div>

        {/* Example Prompts */}
        <div className="mt-8">
          <p 
            className="text-sm mb-3"
            style={{ color: 'var(--color-text-muted)' }}
          >
            Try asking:
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            {[
              '"Create a profile for me"',
              '"Find a time for my group to meet"',
              '"Plan a dinner party"',
              '"Find restaurants near me"'
            ].map((prompt, index) => (
              <span
                key={index}
                className="glass px-3 py-1 rounded-full text-xs"
                style={{
                  backgroundColor: 'rgba(168, 85, 247, 0.1)',
                  border: '1px solid rgba(168, 85, 247, 0.3)',
                  color: 'var(--color-primary)',
                  fontFamily: 'var(--font-family)',
                }}
              >
                {prompt}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
