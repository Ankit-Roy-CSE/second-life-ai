"use client"

import React, { useEffect, useState } from "react"
import { apiClient } from "@/lib/api-client"
import { ListingResponse } from "../../../types/api"
import { ListingChannel, Grade } from "../../../types/enums"
import { ProductCard } from "@/components/features/ProductCard"
import { PageHeader } from "@/components/features/PageHeader"
import { EmptyState } from "@/components/features/EmptyState"
import { ErrorState } from "@/components/features/ErrorState"
import { Skeleton } from "@/components/ui/Skeleton"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs"
import { ShoppingBag } from "lucide-react"

export default function MarketplacePage() {
  const [listings, setListings] = useState<ListingResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchListings = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await apiClient.getMarketplace()
        setListings(data)
      } catch (err: unknown) {
        const error = err as Error
        setError(error.message || "Failed to load marketplace listings.")
      } finally {
        setIsLoading(false)
      }
    }

    fetchListings()
  }, [])

  const filterListings = (channel: ListingChannel | "ALL") => {
    if (channel === "ALL") return listings;
    return listings.filter(l => l.channel === channel);
  }

  return (
    <div className="container mx-auto py-8 max-w-screen-xl px-4 md:px-6">
      <PageHeader 
        title="Marketplace" 
        subtitle="Shop certified refurbished and hyperlocal electronics."
        className="mb-8"
      />

      <Tabs defaultValue="ALL" className="mb-8">
        <TabsList className="mb-6">
          <TabsTrigger value="ALL">All Items</TabsTrigger>
          <TabsTrigger value={ListingChannel.MARKETPLACE}>Marketplace</TabsTrigger>
          <TabsTrigger value={ListingChannel.HYPERLOCAL}>Local Pickup</TabsTrigger>
        </TabsList>

        <TabsContent value="ALL" className="m-0">
          <ListingGrid listings={filterListings("ALL")} isLoading={isLoading} error={error} />
        </TabsContent>
        <TabsContent value={ListingChannel.MARKETPLACE} className="m-0">
          <ListingGrid listings={filterListings(ListingChannel.MARKETPLACE)} isLoading={isLoading} error={error} />
        </TabsContent>
        <TabsContent value={ListingChannel.HYPERLOCAL} className="m-0">
          <ListingGrid listings={filterListings(ListingChannel.HYPERLOCAL)} isLoading={isLoading} error={error} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function ListingGrid({ listings, isLoading, error }: { listings: ListingResponse[], isLoading: boolean, error: string | null }) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-80 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => window.location.reload()} />
  }

  if (listings.length === 0) {
    return (
      <EmptyState 
        icon={ShoppingBag}
        title="No items found" 
        description="There are currently no items listed in this channel." 
      />
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 animate-in fade-in-50 duration-500">
      {listings.map((listing) => (
        <ProductCard 
          key={listing.id}
          product={{ 
            title: listing.product?.title || "Unknown Product", 
            image: undefined // Mock image not provided
          }}
          grade={listing.channel === ListingChannel.HYPERLOCAL ? Grade.B : Grade.A}
          price={listing.price}
          channel={listing.channel}
        />
      ))}
    </div>
  )
}
