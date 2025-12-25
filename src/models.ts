export interface User {
  csrf_token: string;
  is_authenticated: boolean;
  is_active: boolean;
  username: string;
  avatar_url: string;
  can_participate: boolean;
  is_debug: boolean;
}

export interface Country {
  code: string;
  name: string;
}

export interface Season {
  id: number;
  is_closed: boolean;
  member_count: number;
  shipped_count: number;
  delivered_count: number;
  registration_open: string;
  registration_close: string;
  season_close: string;
  is_registration_open: boolean;
  is_matched: boolean;
  gallery_url?: string;
}

export interface Mail {
  id: number;
  is_author: boolean;
  text: string;
  read_date?: string;
  send_date: string;
}

export interface Santa {
  gift_shipped_at?: string;
}

export interface Giftee {
  fullname: string;
  postcode: string;
  address: string;
  country: string;
  gift_delivered_at?: string;
}

export interface Participation {
  fullname: string;
  postcode: string;
  address: string;
  country: string;
  gift_shipped_at?: string;
  gift_delivered_at?: string;
  santa?: Santa;
  giftee?: Giftee;
}

export interface AddressForm {
  fullname?: string;
  postcode?: string;
  address?: string;
  country?: string;
}

export interface AddressFormError {
  fullname?: string[];
  postcode?: string[];
  address?: string[];
}
