"use client"

import React from "react"
import { useMarketplaceListings } from "@/hooks/use-marketplace-listings"
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
  const { data: listings = [], isLoading, isError, error, refetch } = useMarketplaceListings()

  const filterListings = (channel: ListingChannel | "ALL") => {
    if (channel === "ALL") return listings
    return listings.filter(l => l.channel === channel)
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
          <ListingGrid
            listings={filterListings("ALL")}
            isLoading={isLoading}
            isError={isError}
            error={error}
            onRetry={refetch}
          />
        </TabsContent>
        <TabsContent value={ListingChannel.MARKETPLACE} className="m-0">
          <ListingGrid
            listings={filterListings(ListingChannel.MARKETPLACE)}
            isLoading={isLoading}
            isError={isError}
            error={error}
            onRetry={refetch}
          />
        </TabsContent>
        <TabsContent value={ListingChannel.HYPERLOCAL} className="m-0">
          <ListingGrid
            listings={filterListings(ListingChannel.HYPERLOCAL)}
            isLoading={isLoading}
            isError={isError}
            error={error}
            onRetry={refetch}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}

interface ListingGridProps {
  listings: ListingResponse[]
  isLoading: boolean
  isError: boolean
  error: Error | null
  onRetry?: () => void
}

function ListingGrid({ listings, isLoading, isError, error, onRetry }: ListingGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-80 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorState
        message={error?.message ?? "Failed to load listings."}
        onRetry={() => onRetry?.()}
      />
    )
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
            image: undefined, // Mock image not provided
            alt: listing.product?.title || "Product image",
          }}
          grade={listing.channel === ListingChannel.HYPERLOCAL ? Grade.B : Grade.A}
          price={listing.price}
          channel={listing.channel}
        />
      ))}
    </div>
  )
}
