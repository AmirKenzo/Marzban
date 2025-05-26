import Logo from '@/assets/logo.svg?react'
import { GithubStar } from '@/components/github-star'
import { Language } from '@/components/Language'
import { NavMain } from '@/components/nav-main'
import { NavSecondary } from '@/components/nav-secondary'
import { NavUser } from '@/components/nav-user'
import { ThemeToggle } from '@/components/theme-toggle'
import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarRail, SidebarTrigger } from '@/components/ui/sidebar'
import { DISCUSSION_GROUP, DOCUMENTATION, DONATION_URL, REPO_URL } from '@/constants/Project'
import { useAdmin } from '@/hooks/use-admin'
import useDirDetection from '@/hooks/use-dir-detection'
import { getSystemStats } from '@/service/api'
import { BookOpen, Cpu, FileText, GithubIcon, LayoutTemplate, LifeBuoy, ListTodo, Palette, PieChart, RssIcon, Settings, Settings2, Share2Icon, UserCog, Users2, UsersIcon } from 'lucide-react'
import * as React from 'react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const isRTL = useDirDetection() === 'rtl'
  const { t } = useTranslation()
  const [version, setVersion] = useState<string>('')
  const { admin } = useAdmin()

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const data = await getSystemStats()
        if (data?.version) {
          setVersion(` (v${data.version})`)
        }
      } catch (error) {
        console.error('Failed to fetch version:', error)
      }
    }
    fetchVersion()
  }, [])

  const data = {
    user: {
      name: admin?.username || 'Admin',
    },
    navMain: [
      {
        title: 'statistics',
        url: '/statistics',
        icon: PieChart,
      },
      {
        title: 'users',
        url: '/',
        icon: UsersIcon,
      },
      ...(admin?.is_sudo
        ? [
            {
              title: 'hosts',
              url: '/hosts',
              icon: ListTodo,
            },
            {
              title: 'groups',
              url: '/groups',
              icon: Users2,
            },
            {
              title: 'templates.title',
              url: '/templates',
              icon: LayoutTemplate,
            },
            {
              title: 'nodes.title',
              url: '/nodes',
              icon: Share2Icon,
              items: [
                {
                  title: 'nodes.title',
                  url: '/nodes',
                  icon: Share2Icon,
                },
                {
                  title: 'settings.cores.title',
                  url: '/nodes/cores',
                  icon: Cpu,
                },
                {
                  title: 'nodes.logs.title',
                  url: '/nodes/logs',
                  icon: FileText,
                },
              ],
            },
            {
              title: 'admins.title',
              url: '/admins',
              icon: UserCog,
            },
            {
              title: 'settings',
              url: '/settings',
              icon: Settings2,
              items: [
                {
                  title: 'general',
                  url: '/settings',
                  icon: Settings,
                },
                {
                  title: 'theme.title',
                  url: '/settings/theme',
                  icon: Palette,
                },
              ],
            },
          ]
        : []),
    ],
    navSecondary: [
      {
        title: 'Support Us',
        url: DONATION_URL,
        icon: LifeBuoy,
        target: '_blank',
      },
    ],
    community: [
      {
        title: 'documentation',
        url: DOCUMENTATION,
        icon: BookOpen,
        target: '_blank',
      },
      {
        title: 'discussionGroup',
        url: DISCUSSION_GROUP,
        icon: RssIcon,
        target: '_blank',
      },
      {
        title: 'github',
        url: REPO_URL,
        icon: GithubIcon,
        target: '_blank',
      },
    ],
  }

  return (
    <>
      <div className="sticky top-0 z-30 bg-neutral-200/75 dark:bg-neutral-900/75 backdrop-blur flex lg:hidden border-b border-sidebar-border py-3 px-4 justify-between items-center">
        <div className="flex gap-2 items-center">
          <Logo className="!w-4 !h-4 stroke-[2px]" />
          <span className="text-sm font-bold">{t('marzban')}</span>
        </div>
        <SidebarTrigger />
      </div>
      <Sidebar variant="sidebar" {...props} className="border-sidebar-border p-0" side={isRTL ? 'right' : 'left'}>
        <SidebarRail />
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton size="lg" asChild>
                <a href={REPO_URL} target="_blank" className="!gap-0">
                  <Logo className="!w-5 !h-5 stroke-[2px]" />
                  <span className="truncate font-semibold text-sm leading-tight ltr:ml-2 rtl:mr-2">{t('marzban')}</span>
                  <span className="text-xs opacity-45 ltr:ml-1 rtl:mr-1">{version}</span>
                </a>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>
        <SidebarContent>
          <NavMain items={data.navMain} />
          <NavSecondary items={data.community} label="Community" />
          <NavSecondary items={data.navSecondary} className="mt-auto" />
          <div className="flex justify-between px-4 [&>:first-child]:[direction:ltr]">
            <GithubStar />
            <div className="flex gap-2 items-start">
              <Language />
              <ThemeToggle />
            </div>
          </div>
        </SidebarContent>
        <SidebarFooter>
          <NavUser admin={admin} username={data?.user} />
        </SidebarFooter>
      </Sidebar>
    </>
  )
}
