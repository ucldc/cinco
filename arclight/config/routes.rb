Rails.application.routes.draw do
  get "/about", to: "about", controller: "static_pages"
  get "/help", to: "help", controller: "static_pages"
  get "/terms", to: "termsofuse", controller: "static_pages", as: "termsofuse"
  get "/privacy", to: "privacy", controller: "static_pages"
  get "/example", to: "example", controller: "static_pages"
  get "/overview", to: "overview", controller: "static_pages"

  get "/institutions/", to: "arclight/repositories#index"
  get "/institutions/:id", to: "arclight/repositories#show", as: "repository"

  mount Blacklight::Engine => "/"
  mount Arclight::Engine => "/"

  root to: "home", controller: "static_pages"
  concern :searchable, Blacklight::Routes::Searchable.new

  resource :catalog, only: [], as: "catalog", path: "/search", controller: "catalog" do
    concerns :searchable
  end
  devise_for :users

  get "/findaid/:id/entire_text/", to: "static_finding_aid#show", as: "static_finding_aid"
  get "/findaid/:id/entire_text/", to: "static_finding_aid#show", as: "static_finding_aid_redirect",  constraints: { id: /ark\:\/.+/ }

  get "/findaid/*ark", to: "arks#findaid", constraints: { ark: /ark\:\/.+/ }
  get "/findaid", to:  "static_finding_aid#index"


  concern :exportable, Blacklight::Routes::Exportable.new
  concern :hierarchy, Arclight::Routes::Hierarchy.new

  resources :solr_documents, only: [ :show ], path: "/findaid", controller: "catalog" do
  concerns :hierarchy
    concerns :exportable
  end


  resources :bookmarks, only: [ :index, :update, :create, :destroy ] do
    concerns :exportable

    collection do
      delete "clear"
    end
  end

  namespace :contact_form, path: "/contact", as: "contact_form" do
    get "/", action: :new, as: ""
    post "/create", action: :create, as: "create"
  end

  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check

  # Render dynamic PWA files from app/views/pwa/*
  get "service-worker" => "rails/pwa#service_worker", as: :pwa_service_worker
  get "manifest" => "rails/pwa#manifest", as: :pwa_manifest
end
