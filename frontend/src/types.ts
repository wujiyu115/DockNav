export interface Service {
  name: string;
  image: string;
  state: string;
  port: number;
  scheme: 'http' | 'https';
  href: string;
  icon: string;
  online: boolean;
  ports: number[];
}

export interface ServicesResponse {
  host: string;
  count: number;
  services: Service[];
}
