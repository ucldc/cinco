# frozen_string_literal: true

require 'rails_helper'

RSpec.describe CollectionTabsComponent, type: :component do
  subject(:component) { described_class.new(document: document, access: access) }

  let(:document) { SolrDocument.new document: collection, **attr }
  let(:attr) { {} }
  let(:repository_config) do
      instance_double(Arclight::Repository, request_config_present?: true,
                                            available_request_types: [ 'aeon_web_ead' ],
                                            request_config_for_type: {})
    end
let(:collection) do
  { normalized_title: 'Collection Title',
    unitid: 'ARS123',
    collection_unitid: 'ARS123',
    total_component_count: '10',
    online_item_count: '4',
    last_indexed: Time.zone.parse('2025-04-07'),
    collection?: true,
    requestable?: true,
    repository_config:,
    ead_file: 'ars123.xml'
  }
end

let(:access) { "some access content" }

   before do
    render_inline(component)
  end

  it 'renders a summary tab' do
    expect(page).to have_css('#nav-summary-tab', text: 'Summary')
  end
  it 'renders a Details tab' do
    expect(page).to have_css('#nav-details-tab', text: 'Details')
  end
  it 'renders a Contents tab' do
    expect(page).to have_css('#nav-content-tab', text: 'Contents')
  end
  it 'renders a Access and Use tab' do
    expect(page).to have_css('#nav-access-and-use-tab', text: 'Access and Use')
  end
  it 'renders a Companion Guides tab' do
    expect(page).to have_css('#nav-companion-guides-tab', text: 'Companion Guides')
  end
end
