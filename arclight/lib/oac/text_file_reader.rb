module Arclight
  class TextFileReader
    # @param `record`
    def initialize(record)
      @directory = ENV.fetch('TEXT_FILE_DIR', '/app/files/text/')

      items = record.xpath('/ead/archdesc/otherfindaid/list/item')
      @file_ids = items.map do |item|
        href = item.xpath('./extref').attr("href").value
        href.split("/")[-1].split(".")[0]
      end
    end

    attr_reader :directory, :file_ids

    def get_texts
      file_ids.map { |file_id|
        File.read(File.join(directory, file_id + ".txt"))
      }
    end
  end
end
