module Oac
  class TextFileReader
    # @param `record`
    def initialize(base_file)
      base_dir = base_file.split("/")[0...-1].join("/") + "/"
      @directory = ENV.fetch("TEXT_FILE_DIR", base_dir)
      @filename = ENV.fetch("TEXT_FILE_NAME", "extracted-supplementary-files-text.txt")
    end

    attr_reader :directory, :filename

    def get_text
      filepath = File.join(directory, filename)
      if File.exist?(filepath)
        File.read(filepath)
      else
        ""
      end
    end
  end
end
