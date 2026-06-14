import React from "react"
import Image from "next/image"
import { Card, CardContent } from "@/components/ui/Card"
import { GradeBadge } from "@/components/ui/GradeBadge"
import { Badge } from "@/components/ui/Badge"
import { Grade, ListingChannel } from "../../../types/enums"

export interface ProductCardProps {
  product: {
    title: string;
    image?: string;
  };
  grade: Grade;
  price: number;
  channel: ListingChannel;
}

export function ProductCard({ product, grade, price, channel }: ProductCardProps) {
  const isHyperlocal = channel === ListingChannel.HYPERLOCAL;

  return (
    <Card className="overflow-hidden flex flex-col transition-all hover:border-primary/50 hover:shadow-md">
      <div className="relative aspect-square w-full bg-muted border-b border-border">
        {product.image ? (
          <Image src={product.image} alt={product.title} fill className="object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            No image
          </div>
        )}
        <div className="absolute top-3 right-3 flex flex-col gap-2">
          <GradeBadge grade={grade} size="sm" showLabel={false} className="shadow-sm" />
        </div>
        <div className="absolute top-3 left-3">
          {isHyperlocal ? (
            <Badge variant="info" className="shadow-sm">Local Pickup</Badge>
          ) : (
            <Badge variant="default" className="shadow-sm">Marketplace</Badge>
          )}
        </div>
      </div>
      <CardContent className="p-5 flex flex-col flex-1 bg-card">
        <h4 className="font-semibold text-lg line-clamp-2 mb-2">{product.title}</h4>
        <div className="mt-auto pt-4 flex items-center justify-between border-t border-border">
          <span className="text-xl font-bold">${price.toFixed(2)}</span>
          <span className="text-sm text-muted-foreground font-medium">
            {isHyperlocal ? "Save on shipping" : "Free shipping"}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
