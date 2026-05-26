import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  try {
    const { data, error } = await supabase.auth.getUser()
    if (error) {
      console.error('Supabase getUser error:', error.message)
      redirect('/login')
    }

    const user = data?.user
    if (!user) redirect('/login')
  } catch (err) {
    console.error('Unexpected auth error in DashboardLayout:', err)
    redirect('/login')
  }

  return <>{children}</>
}
