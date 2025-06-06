import { extendTheme } from '@chakra-ui/react'

export const theme = extendTheme({
  config: {
    initialColorMode: 'dark',
    useSystemColorMode: false,
  },
  styles: {
    global: {
      html: {
        overflowX: 'hidden',
      },
      body: {
        bg: 'gray.50',
        overflowX: 'hidden',
        width: '100%',
        minHeight: '100vh',
      },
      '#root': {
        width: '100%',
        minHeight: '100vh',
      },
    },
  },
  components: {
    Container: {
      baseStyle: {
        maxW: 'container.xl',
        px: { base: 4, md: 6 },
      },
    },
  },
}) 