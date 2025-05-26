import PageHeader from '@/components/page-header'
import { Plus } from 'lucide-react'
import MainSection from '@/components/hosts/Hosts'
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getHosts, createHost, modifyHost, CreateHost, ProxyHostALPN, ProxyHostFingerprint, MultiplexProtocol, Xudp, BaseHost } from '@/service/api'
import { HostFormValues } from '@/components/hosts/Hosts'
import { toast } from 'sonner'
import { useTranslation } from 'react-i18next'
import { Separator } from '@/components/ui/separator'
import { Card, CardContent } from '@/components/ui/card'

export default function HostsPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingHost, setEditingHost] = useState<BaseHost | null>(null)
  const { data, isLoading } = useQuery({
    queryKey: ['getGetHostsQueryKey'],
    queryFn: () => getHosts(),
  })
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const handleDialogOpen = (open: boolean) => {
    setIsDialogOpen(open)
    if (!open) {
      setEditingHost(null)
    }
  }

  const handleCreateClick = () => {
    setEditingHost(null)
    setIsDialogOpen(true)
  }

  const onAddHost = (open: boolean) => {
    setIsDialogOpen(open)
  }

  const handleSubmit = async (formData: HostFormValues) => {
    try {
      // Check if all protocols are set to none
      const allProtocolsNone =
        formData.mux_settings &&
        (!formData.mux_settings.sing_box?.protocol || formData.mux_settings.sing_box.protocol === 'none') &&
        (!formData.mux_settings.clash?.protocol || formData.mux_settings.clash.protocol === 'none') &&
        !formData.mux_settings.xray?.concurrency

      // If creating a new host, set priority to max+1
      let priority = formData.priority
      if (!editingHost?.id && data && data.length > 0) {
        const maxPriority = Math.max(...data.map(h => h.priority ?? 0))
        priority = maxPriority + 1
      }

      // Convert HostFormValues to CreateHost type
      const hostData: CreateHost = {
        ...formData,
        priority,
        alpn: formData.alpn as ProxyHostALPN | undefined,
        fingerprint: formData.fingerprint as ProxyHostFingerprint | undefined,
        mux_settings: allProtocolsNone
          ? undefined
          : formData.mux_settings
            ? {
                ...formData.mux_settings,
                sing_box: formData.mux_settings.sing_box
                  ? {
                      protocol: formData.mux_settings.sing_box.protocol === 'none' ? undefined : (formData.mux_settings.sing_box.protocol as MultiplexProtocol),
                      max_connections: formData.mux_settings.sing_box.max_connections || undefined,
                      max_streams: formData.mux_settings.sing_box.max_streams || undefined,
                      min_streams: formData.mux_settings.sing_box.min_streams || undefined,
                      padding: formData.mux_settings.sing_box.padding || undefined,
                      brutal: formData.mux_settings.sing_box.brutal || undefined,
                    }
                  : undefined,
                clash: formData.mux_settings.clash
                  ? {
                      protocol: formData.mux_settings.clash.protocol === 'none' ? undefined : (formData.mux_settings.clash.protocol as MultiplexProtocol),
                      max_connections: formData.mux_settings.clash.max_connections || undefined,
                      max_streams: formData.mux_settings.clash.max_streams || undefined,
                      min_streams: formData.mux_settings.clash.min_streams || undefined,
                      padding: formData.mux_settings.clash.padding || undefined,
                      brutal: formData.mux_settings.clash.brutal || undefined,
                      statistic: formData.mux_settings.clash.statistic || undefined,
                      only_tcp: formData.mux_settings.clash.only_tcp || undefined,
                    }
                  : undefined,
                xray: formData.mux_settings.xray
                  ? {
                      concurrency: formData.mux_settings.xray.concurrency || undefined,
                      xudp_concurrency: formData.mux_settings.xray.xudp_concurrency || undefined,
                      xudp_proxy_443: formData.mux_settings.xray.xudp_proxy_443 === 'none' ? undefined : (formData.mux_settings.xray.xudp_proxy_443 as Xudp),
                    }
                  : undefined,
              }
            : undefined,
        fragment_settings: formData.fragment_settings
          ? {
              xray: formData.fragment_settings.xray
                ? {
                    packets: formData.fragment_settings.xray.packets || '',
                    length: formData.fragment_settings.xray.length || '',
                    interval: formData.fragment_settings.xray.interval || '',
                  }
                : undefined,
            }
          : undefined,
      }

      if (editingHost?.id) {
        // This is an edit operation
        await modifyHost(editingHost.id, hostData)
        return { status: 200 }
      } else {
        // This is a new host
        await createHost(hostData)
        return { status: 200 }
      }
    } catch (error: any) {
      console.error('Error submitting host:', error)

      // Improved error extraction for backend schema
      let errorMessage = ''

      // 1. FastAPI/DRF style: error.response.data.detail (could be string or array)
      if (error?.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Join all error messages
          errorMessage = error.response.data.detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join('\n')
        } else if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail
        } else {
          errorMessage = JSON.stringify(error.response.data.detail)
        }
      }
      // 2. Common: error.response.data.message
      else if (error?.response?.data?.message) {
        errorMessage = error.response.data.message
      }
      // 3. Fallback: error.message
      else if (error?.message) {
        errorMessage = error.message
      }
      // 4. Last resort: translation fallback
      else {
        errorMessage = editingHost?.id ? t('hostsDialog.editFailed', { name: formData.remark }) : t('hostsDialog.createFailed', { name: formData.remark })
      }

      toast.error(errorMessage)
      return { status: 500 }
    } finally {
      // Refresh the hosts data
      queryClient.invalidateQueries({
        queryKey: ['/api/hosts'],
      })
    }
  }

  return (
    <div className="pb-8 flex flex-col gap-2 w-full items-start">
      <div className="w-full transform-gpu animate-fade-in" style={{ animationDuration: '400ms' }}>
        <PageHeader title="hosts" description="manageHosts" buttonIcon={Plus} buttonText="hostsDialog.addHost" onButtonClick={handleCreateClick} />
        <Separator />
      </div>

      <div className="px-4 w-full pt-6">
        {isLoading ? (
          <div className="w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 py-6">
            {Array.from({ length: 6 }).map((_, index) => (
              <Card key={index} className="animate-pulse">
                <CardContent className="p-4">
                  <div className="flex flex-col gap-2">
                    <div className="h-5 bg-muted rounded-md w-2/3"></div>
                    <div className="h-3 bg-muted rounded-md w-full"></div>
                    <div className="h-3 bg-muted rounded-md w-4/5"></div>
                    <div className="flex justify-between mt-2">
                      <div className="h-6 bg-muted rounded-md w-1/4"></div>
                      <div className="h-6 bg-muted rounded-md w-1/4"></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <MainSection
            data={data || []}
            isDialogOpen={isDialogOpen}
            onDialogOpenChange={handleDialogOpen}
            onAddHost={onAddHost}
            onSubmit={handleSubmit}
            editingHost={editingHost}
            setEditingHost={setEditingHost}
          />
        )}
      </div>
    </div>
  )
}
